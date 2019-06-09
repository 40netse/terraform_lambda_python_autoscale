import boto3
import json

from django.http import HttpResponseBadRequest, HttpResponse
import time
from .const import *
import base64

from .fos_api import FortiOSAPI
from .Fortigate import Fortigate
from .RouteTable import RouteTable
from boto3.dynamodb.conditions import Key, Attr
from botocore.exceptions import ClientError


class AutoScaleGroup(object):
    def __init__(self, data, asg_name=None):
        if data is not None:
            if 'TopicArn' not in data:
                return
            if 'Type' not in data:
                return
        self.status = None
        self.asg = None
        self.asg_info = None
        self.table = None
        self.route_tables = None
        self.instance_id_tables = None
        self.endpoint_url = None
        self.master_ip = None
        self.private_subnet_id = None
        self.api = None
        self.db_resource = boto3.resource('dynamodb')
        self.db_client = boto3.client('dynamodb')
        self.asg_client = boto3.client('autoscaling')
        self.ec2_client = boto3.client('ec2')
        self.ec2_resource = boto3.resource('ec2')
        self.s3_client = boto3.client('s3')
        self.s3_resource = boto3.resource('s3')
        self.elbv2_client = boto3.client('elbv2')
        self.unused_licenses = []
        self.region = None
        self.account = None
        self.target_group = None
        if data is not None:
            p = data['TopicArn'].split(':')
            if len(p) != 6:
                self.name = None
            else:
                self.name = p[5]
                self.account = p[4]
                self.region = p[3]
        else:
            self.name = asg_name
            self.table = self.db_resource.Table(self.name)
            try:
                r = self.table.get_item(TableName=self.name, Key={"Type": TYPE_AUTOSCALE_GROUP, "TypeId": "0000"})
            except self.db_client.exceptions.ResourceNotFoundException:
                r = None
            if r is not None and 'ResponseMetadata' in r:
                status = r['ResponseMetadata']['HTTPStatusCode']
                if status == STATUS_OK:
                    if 'Item' in r:
                        self.asg = r['Item']
                        if 'EndPointUrl' in self.asg:
                            self.endpoint_url = self.asg['EndPointUrl']
                        if 'TargetGroup' in self.asg:
                            self.target_group = self.asg['TargetGroup']
        self.update_asg_info()
        if data is not None:
            if data['Type'] == 'Notification':
                self.table = self.db_resource.Table(self.name)
                try:
                    r = self.table.get_item(TableName=self.name,
                                            Key={"Type": TYPE_AUTOSCALE_GROUP, "TypeId": "0000"})
                except self.db_client.exceptions.ResourceNotFoundException:
                    r = None
                if r is not None and 'ResponseMetadata' in r:
                    status = r['ResponseMetadata']['HTTPStatusCode']
                    if status == STATUS_OK:
                        if 'Item' in r:
                            self.asg = r['Item']
                            if 'EndPointUrl' in self.asg:
                                self.endpoint_url = self.asg['EndPointUrl']
                            if 'TargetGroup' in self.asg:
                                self.target_group = self.asg['TargetGroup']
        if self.table is not None:
            t = self.table
            try:
                r = t.query(KeyConditionExpression=Key('Type').eq(TYPE_ROUTETABLE_ID))
            except self.db_client.exceptions.ResourceNotFoundException:
                return
            if 'Items' in r:
                if len(r['Items']) > 0:
                    self.route_tables = []
                for rt in r['Items']:
                    self.route_tables.append(rt)
            try:
                i = t.query(KeyConditionExpression=Key('Type').eq(TYPE_INSTANCE_ID))
            except self.db_client.exceptions.ResourceNotFoundException:
                return
            if 'Items' in i:
                if len(i['Items']) > 0:
                    self.instance_id_tables = []
                    for instance in i['Items']:
                        self.instance_id_tables.append(instance)
            if data is not None:
                if data['Type'] == 'SubscriptionConfirmation':
                    logger.debug('AutoscaleGroup Init Subscription Confirmation')
                    autoscale_group_wait_count = 5
                    while autoscale_group_wait_count > 0:
                        r = self.asg_client.describe_auto_scaling_groups(AutoScalingGroupNames=[self.name])
                        logger.debug('AutoscaleGroup Init Sub 1: group_wait_count = %d' % autoscale_group_wait_count)
                        if 'AutoScalingGroups' not in r:
                            logger.debug('AutoscaleGroup Init Subscription Confirmation 2')
                            time.sleep(3)
                            autoscale_group_wait_count = autoscale_group_wait_count - 1
                            continue
                        if len(r['AutoScalingGroups']) == 0:
                            logger.debug('AutoscaleGroup Init Subscription Confirmation 3')
                            time.sleep(3)
                            autoscale_group_wait_count = autoscale_group_wait_count - 1
                            continue
                        autoscale_group_wait_count = 0
        return

    def __repr__(self):
        return ' () ' % ()

    def update_asg_info(self):
        try:
            r = self.asg_client.describe_auto_scaling_groups(AutoScalingGroupNames=[self.name])
        except Exception as ex:
            logger.exception("exeception - describe_auto_scaling_groups(): ex = %s" % ex)
            return
        if len(r['AutoScalingGroups']) > 1:
            return
        self.asg_info = r['AutoScalingGroups'][0]

    #
    # Find a tag that matches key on this Fortigate
    #
    def get_tag(self, key):
        if self.asg_info is None:
            self.update_asg_info()
        if 'Tags' not in self.asg_info:
            return None
        tags = self.asg_info['Tags']
        for t in tags:
            if t['Key'] == key:
                return t['Value']
        return None

    #
    # This is used during a subscription notification to update the min,desired counts in the Autoscale Group
    # during Development, set the min=1 to save EC2 expense
    # during Production, set the min = the number of AZ to provide AZ redundancy
    #
    def update_instance_counts(self):
        size = 0
        aws_asg = self.asg_client.describe_auto_scaling_groups(AutoScalingGroupNames=[self.name])
        if 'AutoScalingGroups' in aws_asg:
                if len(aws_asg['AutoScalingGroups']) == 0:
                    time.sleep(3)
                    return False
                if len(aws_asg['AutoScalingGroups']) > 0:
                    size = len(aws_asg['AutoScalingGroups'][0]['AvailabilityZones'])
        #
        # TODO: change back to size for production
        #
        size = len(aws_asg)
        logger.debug('update_instance_count: name = %s, size = %d' % (self.name, size))
        try:
            self.asg_client.update_auto_scaling_group(AutoScalingGroupName=self.name,
                                                      MinSize=size, DesiredCapacity=size)
        except Exception as ex:
            logger.exception("exeception - update_auto_scaling_group(): ex = %s" % ex)
            return False
        return True

    def delete_table(self):
        table_found = True
        t = None
        try:
            t = self.db_client.describe_table(TableName=self.name)
            if 'ResponseMetadata' in t:
                if t['ResponseMetadata']['HTTPStatusCode'] == STATUS_OK:
                    table_found = True
        except self.db_client.exceptions.ResourceNotFoundException:
            table_found = False
        if table_found is True:
            if 'Table' in t and t['Table']['TableStatus'] == 'ACTIVE':
                logger.debug('delete_table(): Table Found for SubscriptionRequest - table = %s' % self.name)
                self.db_client.delete_table(TableName=self.name)
                self.status = 'DELETING'
                while self.status == 'DELETING':
                    time.sleep(3)
                    try:
                        t = self.db_client.describe_table(TableName=self.name)
                    except self.db_client.exceptions.ResourceNotFoundException:
                        return
                    if 'Table' in t and 'TableStatus' in t['Table']:
                        self.status = t['Table']['TableStatus']

    def find_s3_license_file(self, bucket):
        if bucket is None:
            return None
        s3c = self.s3_client
        if s3c is None:
            return None
        s3buckets = s3c.list_buckets()
        s3lbucket_exists = False
        if 'Buckets' in s3buckets:
            for b in s3buckets['Buckets']:
                if 'Name' in b:
                    if b['Name'] == bucket:
                        s3lbucket_exists = True
                        break
        if s3lbucket_exists is False:
            return None
        objects = s3c.list_objects(Bucket=bucket)
        if 'Contents' not in objects:
            return None
        for o in objects['Contents']:
            suffix = o['Key'].split('.')
            if len(suffix) == 2 and suffix[1] == 'lic':
                self.write_license_to_db(bucket, o['Key'])

    def assign_license_to_instance(self, fortigate):
        if fortigate.ec2 is None:
            return
        t = self.db_resource.Table(self.name)
        try:
            results = t.query(TableName=self.name, KeyConditionExpression=Key('Type').eq(TYPE_BYOL_LICENSE))
        except Exception as e:
            logger.exception('no licenses found(): autoscale scale group = %s' % e)
            return None
        l = None
        for l in results['Items']:
            if l['InstanceOwner'] == 'unused':
                break
        if l is None or 'Bucket' not in l:
            return None
        bucket = l['Bucket']
        object_key = l['TypeId']
        user = 'admin'
        password = 'Password123!'
        s3c = self.s3_client
        f = object_key.split('/')
        file = '/tmp/' + f[1]
        with open(file, 'wb') as content:
            try:
                status = s3c.download_fileobj(bucket, object_key, content)
            except Exception as ex:
                logger.exception("caught: %s with PutLicenseInfo" % ex.message)
        b64lic = base64.b64encode(open(file).read().encode()).decode()
        ip = None
        if 'PublicIpAddress' in fortigate.ec2:
            ip = fortigate.ec2['PublicIpAddress']
        elif 'PrivateIpAddress' in self.ec2:
            ip = fortigate.ec2['PrivateIpAddress']
        instance_id = fortigate.instance_id
        fortigate.api = FortiOSAPI()
        fortigate.api.login(ip, 'admin', 'Password123!')
        #fortigate.api.login(user, password, verbose, debug)

        #status = fortigate.api.post('/api/v2/monitor/system/vmlicense/upload', params, data={"file_content": lic})
        status = fortigate.api.post(api='monitor', path='system', name='vmlicense',
                                    action='upload', data={"file_content": b64lic})
        logger.debug("PutLicense: %s status = %s" % (fortigate.instance_id, status))
        self.write_license_to_db(bucket=bucket, key=l['TypeId'], instance_id=instance_id)
        return status

    def write_license_to_db(self, bucket, key, instance_id=None):
        table_found = True
        try:
            t = self.db_client.describe_table(TableName=self.name)
            if 'ResponseMetadata' in t:
                if t['ResponseMetadata']['HTTPStatusCode'] == STATUS_OK:
                    table_found = True
        except self.db_client.exceptions.ResourceNotFoundException:
            table_found = False
        if table_found is False:
            return None
        if self.table is None:
            self.table = self.db_resource.Table(self.name)
        try:
            r = self.table.get_item(TableName=self.name, Key={"Type": TYPE_BYOL_LICENSE, "TypeId": key})
        except self.db_client.exceptions.ResourceNotFoundException:
            r = None
        if r is not None and 'Item' in r:
            size = r['Item']['Size']
            lf = r['Item']
        else:
            size = 0
            lf = None
        if instance_id is None and lf is not None:
            return STATUS_OK
        if instance_id is None:
            owner = "unused"
            ldb = {"Type": TYPE_BYOL_LICENSE, "TypeId": key, "Bucket": bucket,
                   "Size": size, "InstanceOwner": owner}
            try:
                self.table.put_item(Item=ldb)
            except Exception as e:
                logger.exception('exception write_license_to_db():  e = %s' % e)
                return None
        else:
            owner = r['Item']['InstanceOwner']
            if owner == 'unused':
                owner = instance_id
                ldb = {"Type": TYPE_BYOL_LICENSE, "TypeId": key, "Bucket": bucket,
                     "Size": size, "InstanceOwner": owner}
                try:
                    self.table.put_item(Item=ldb)
                except Exception as e:
                    logger.exception('exception write_license_to_db():  e = %s' % e)
                    return None
        return STATUS_OK

    def write_to_db(self, data, url=None):
        if self.name is None:
            return
        if 'Type' not in data:
            return
        if 'Token' not in data:
            return
        notification_type = data['Type']
        subscribe_url = data['SubscribeURL']
        table_found = True
        t = None
        try:
            t = self.db_client.describe_table(TableName=self.name)
            if 'ResponseMetadata' in t:
                if t['ResponseMetadata']['HTTPStatusCode'] == STATUS_OK:
                    table_found = True
        except self.db_client.exceptions.ResourceNotFoundException:
            table_found = False
        if table_found is False:
            self.db_client.create_table(AttributeDefinitions=attribute_definitions,
                                        TableName=self.name, KeySchema=schema,
                                        ProvisionedThroughput=provisioned_throughput)
            self.status = 'CREATING'
            while self.status == 'CREATING':
                time.sleep(3)
                t = self.db_client.describe_table(TableName=self.name)
                if 'Table' in t and 'TableStatus' in t['Table']:
                    self.status = t['Table']['TableStatus']
        if 'Table' in t and 'TableStatus' in t['Table']:
            self.status = t['Table']['TableStatus']
        if self.table is None:
            self.table = self.db_resource.Table(self.name)
        try:
            r = self.table.get_item(TableName=self.name, Key={"Type": TYPE_AUTOSCALE_GROUP, "TypeId": "0000"})
        except self.db_client.exceptions.ResourceNotFoundException:
            r = None
        if r is not None and 'ResponseMetadata' in r:
            status = r['ResponseMetadata']['HTTPStatusCode']
            if status == STATUS_OK:
                if 'Item' in r:
                    if notification_type == 'SubscriptionConfirmation':
                        #
                        # Already subscribed. Why are we getting this?
                        #
                        self.asg = r['Item']
                        return
                    elif notification_type == 'Notification':
                        self.asg = r['Item']
                        return
                    else:
                        #
                        # not SUBSCRIBE or NOTIFY
                        #
                        self.asg = None
                else:
                    if notification_type == 'NOTIFY':
                        self.asg = None
                        return
        #
        # Type is SUBSCRIBE and the Subscribe Entry is not in the DB
        #
        if self.asg is None:
            self.asg = {"Type": TYPE_AUTOSCALE_GROUP, "TypeId": "0000",
                        "AutoScaleGroupName": self.name, "SubscribeURL": subscribe_url,
                        "TimeStamp": data['Timestamp'], "UpdateCounts": "False"}
            if url is not None:
                self.asg.update({"EndPointUrl": url})
            target_group = self.get_tag('Fortigate-Target-Group-Name')
            if target_group is not None:
                self.asg.update({"TargetGroup": target_group})
            else:
                self.asg.update({"TargetGroup": self.name})
            try:
                r = self.table.put_item(Item=self.asg)
            except self.db_client.exceptions.ResourceNotFoundException:
                return
            if r is not None and 'ResponseMetadata' in r:
                if 'HTTPStatusCode' in r['ResponseMetadata']:
                    status = r['ResponseMetadata']['HTTPStatusCode']
                    if status != STATUS_OK:
                        self.asg = None
                    self.status = 'ACTIVE'

        return

    #
    # Lifecycle Hook Launch message: create second nic, attach to private subnet,
    #   put instance_id in DB, return OK to respond to lifecycle hook
    #
    # If this is the first LifeCycleHook call, use the metadata (list of subnets)
    # passed in by CFT or Terraform to find all the route tables used by this VPC.
    #
    def lch_launch(self, data):
        if 'Message' not in data:
            return STATUS_OK
        try:
            msg = json.loads(data['Message'])
        except ValueError:
            logger.warning('sns(): Notification Not Valid JSON: {}'.format(data['Message']))
            return STATUS_OK
        if 'NotificationMetadata' not in msg:
            logger.warning('lch_launch(): no metadata in lch launch notification')
            return STATUS_OK
        f = Fortigate(data, self)
        logger.info('lch_launch(): Fortigate = %s, lch_token = %s' % (f, f.lch_token))
        metadata = msg['NotificationMetadata']
        subnets = metadata.split(":")
        if self.route_tables is None:
            i = 0
            self.route_tables = []
            #
            # Only lookup route table for 1 indexed subnets (Private Subnets)
            #
            while i < len(subnets):
                odd = i % 2
                if odd:
                    r = RouteTable(self, subnets[i])
                    if r.route_table_id is not None:
                        r.write_to_db()
                        rt = {"Subnet": r.subnet_id, "TypeId": r.route_table_id, "NetworkInterfaceId": r.eni}
                        self.route_tables.append(rt)
                i = i + 1
        logger.info('lch_launch(): subnets = %s' % subnets)
        rc = f.attach_second_interface(subnets)
        if rc == STATUS_OK:
            instance = {"Type": TYPE_INSTANCE_ID, "TypeId": f.instance_id,
                        "AutoScaleGroupName": self.name, "State": "LCH_LAUNCH",
                        "PrivateSubnetId": f.private_subnet_id, "CountDown": 60,
                        "SecondENIId": f.second_nic_id, "TimeStamp": f.timestamp}
            self.table.put_item(Item=instance)
        self.verify_route_tables()
        return STATUS_OK

    def lch_terminate(self, data):
        f = Fortigate(data, self)
        logger.info('lch_terminate(): instance = %s, second_eni = %s' % (f.instance_id, f.second_nic_id))
        if f.auto_scale_group is None:
            return
        f.detach_second_interface()
        return STATUS_OK

    def remove_master(self):
        logger.info('remove_master(): ')
        try:
            r = self.table.get_item(TableName=self.name, Key={"Type": TYPE_AUTOSCALE_GROUP, "TypeId": "0000"})
        except self.db_client.exceptions.ResourceNotFoundException:
            r = None

        self.table.update_item(Key={"Type": TYPE_AUTOSCALE_GROUP, "TypeId": "0000"},
                               UpdateExpression="remove MasterIp, MasterId")
        return

    def launch_instance(self, data):
        f = Fortigate(data, self)
        if f.ec2 is None:
            return
        num_enis = len(f.ec2['NetworkInterfaces'])
        logger.info('lch_launch_instance(): Fortigate = %s, lch_token = %s, enis = %d, group = %s' %
                    (f, f.lch_token, num_enis, f.auto_scale_group))
        if len(f.ec2['NetworkInterfaces']) < 2:
            self.ec2_client.terminate_instances(InstanceIds=[f.instance_id])
            try:
                self.table.delete_item(Key={"Type": TYPE_INSTANCE_ID, "TypeId": f.instance_id})
            except self.db_client.exceptions.ResourceNotFoundException:
                pass
            return STATUS_OK
        if f.auto_scale_group is None:
            return STATUS_OK
        try:
            r = self.table.get_item(TableName=self.name, Key={"Type": TYPE_INSTANCE_ID, "TypeId": f.instance_id})
        except self.db_client.exceptions.ResourceNotFoundException:
            r = None
        if r is None or 'Item' not in r:
            logger.info('lch_launch_instance1a():')
            return STATUS_OK
        instance = r['Item']
        if instance['State'] == 'LCH_LAUNCH':
            logger.info('lch_launch_instance1a(): Instance Not ready to go InService. i = %s ' % f.instance_id)
            return STATUS_NOT_OK

        key = 'Fortigate-License'
        license_type = f.get_tag(key)
        if license_type == 'byol':
            key = 'Fortigate-S3-License-Bucket'
            license_bucket = f.get_tag(key)
            self.find_s3_license_file(license_bucket)
            self.assign_license_to_instance(f)

        logger.info('lch_launch_instance2(): ')
        try:
            r2 = self.table.get_item(TableName=self.name, Key={"Type": TYPE_AUTOSCALE_GROUP, "TypeId": "0000"})
        except self.db_client.exceptions.ResourceNotFoundException:
            r2 = None
        logger.info('lch_launch_instance3(): ')
        if r2 is not None and 'MasterId' in r2:
            id = r2['MasterId']
            instance_master = None
            try:
                instance_master = self.ec2_client.describe_instances(InstanceIds=[id])
            except Exception as ex:
                logger.exception("Error describing instance: %s, ex = %s" % (id, ex))
                instance_master = None
        if instance_master is None:
            self.remove_master()
        if (r2 is not None) and ('MasterIp' in r2['Item']):
            is_instance_master = False
            self.master_ip = r2['Item']['MasterIp']
            logger.info('lch_launch_instance4(): master_ip = %s' % self.master_ip)
        else:
            is_instance_master = True
            self.master_ip = f.ec2['PrivateIpAddress']
            logger.info('lch_launch_instance4a(): master_ip = %s' % self.master_ip)
            self.table.update_item(Key={"Type": TYPE_AUTOSCALE_GROUP, "TypeId": "0000"},
                                   UpdateExpression="set MasterIp = :m, MasterId = :i, OrigMasterId = :p",
                                   ExpressionAttributeValues={':m': self.master_ip, ':i': f.ec2['InstanceId'],
                                                              ':p': f.ec2['InstanceId']})
            self.asg.update([('MasterId', f.ec2['InstanceId'])])
            logger.info('lch_launch_instance4b(): master_ip = %s' % self.master_ip)
        instance = r['Item']
        instance['State'] = "InService"
        if 'PrivateSubnetId' in instance:
            self.private_subnet_id = instance['PrivateSubnetId']
        logger.info('lch_launch_instance5(): master_ip = %s' % instance)
        self.table.put_item(Item=instance)
        logger.info('lch_launch_instance5a():')
        f.add_member_to_autoscale_group(self.master_ip)
        logger.info('lch_launch_instance6(): master_ip = %s' % instance)
        if 'MasterId' in self.asg and f.ec2['InstanceId'] == self.asg['MasterId']:
            is_instance_master = True
        logger.info('lch_launch_instance7(): is_instance_aster = %s' % is_instance_master)
        if is_instance_master is True:
            self.callback_add_member_to_lb(self.master_ip, is_instance_master)
        logger.info('lch_launch_instance8():')
        return STATUS_OK

    def terminate_instance(self, data):
        f = Fortigate(data, self)
        new_master_pip = None
        self.table.delete_item(Key={"Type": TYPE_INSTANCE_ID, "TypeId": f.instance_id})
        if self.table is not None:
            v = f.get_tag('Fortigate-License')
            if v == 'byol':
                try:
                    results = self.table.query(TableName=self.name, KeyConditionExpression=Key('Type').eq(TYPE_BYOL_LICENSE))
                except Exception as e:
                    logger.exception('no licenses found(): autoscale scale group = %s' % e)
                if results is not None:
                    for lf in results['Items']:
                        if lf['InstanceOwner'] == f.instance_id:
                            lf['InstanceOwner'] = 'unused'
                            self.table.put_item(Item=lf)
            if 'MasterId' in self.asg and f.instance_id == self.asg['MasterId']:
                logger.info("Lost auto-scale Master instance: %s" % f.instance_id)
                try:
                    i = self.table.query(KeyConditionExpression=Key('Type').eq('0010'),
                                         ProjectionExpression="#t, #i",
                                         ExpressionAttributeNames={'#t': 'TypeId', '#i': 'TimeStamp'})
                except self.db_client.exceptions.ResourceNotFoundException:
                    return STATUS_OK
                db_dict = {}
                if i is not None and 'Items' in i:
                    for item in i['Items']:
                        db_dict.update({item['TimeStamp']: item['TypeId']})
                    for entry in sorted(db_dict.keys()):
                        if entry in sorted(db_dict.keys())[0]:
                            logger.debug("New Master %s with oldest timestamp: %s" % (db_dict[entry], entry))
                            # get instance primary private and public ip
                            try:
                                instance = self.ec2_client.describe_instances(InstanceIds=[db_dict[entry]])
                            except Exception as ex:
                                logger.exception("Error describing instance: %s, ex = %s" % (db_dict[entry], ex))
                                return STATUS_OK
                            new_master_pip = instance['Reservations'][0]['Instances'][0]['PrivateIpAddress']
                            new_master_eip = instance['Reservations'][0]['Instances'][0]['PublicIpAddress']
                            # update db: type 0000 with new IP and ID
                            self.table.update_item(Key={"Type": TYPE_AUTOSCALE_GROUP, "TypeId": "0000"},
                                                   UpdateExpression="set MasterIp = :m, MasterId = :i",
                                                   ExpressionAttributeValues={':m': new_master_pip,
                                                                              ':i': db_dict[entry]})
                            # update fortios: set config sys auto-scale as master
                            callback_url = self.asg['EndPointUrl'] + "/callback/" + self.asg['AutoScaleGroupName']
                            data = {
                                  "status": "enable",
                                  "role": "master",
                                  "sync-interface": "port1",
                                  "psksecret": self.asg['AutoScaleGroupName'],
                                  "callback-url": callback_url
                            }
                            logger.info('posting auto-scale config: {}' .format(data))
                            self.api = FortiOSAPI()
                            self.api.login(new_master_eip, 'admin', self.asg['OrigMasterId'])
                            content = self.api.put(api='cmdb', path='system', name='auto-scale', data=data)
                            self.api.logout()
                            logger.info('restapi response: {}' .format(content))
                            # update instance tag: set 'Fortinet-Autoscale' to 'Master'
                            self.ec2_client.create_tags(Resources=[db_dict[entry]],
                                                        Tags=[{'Key': 'Fortinet-Autoscale', 'Value': 'Master'}])
                        else:
                            logger.debug("Existing Slave %s with timestamp: %s" % (db_dict[entry], entry))
                            # get instance primary public ip
                            try:
                                instance = self.ec2_client.describe_instances(InstanceIds=[db_dict[entry]])
                            except Exception as ex:
                                logger.debug("Error describing instance: %s, ex = %s" % (db_dict[entry], ex))
                                return STATUS_OK
                            existing_slave_eip = instance['Reservations'][0]['Instances'][0]['PublicIpAddress']
                            # update fortios: set config sys auto-scale to point to new master
                            try:
                                r2 = self.table.get_item(TableName=self.name, Key={"Type": TYPE_AUTOSCALE_GROUP,
                                                                                   "TypeId": "0000"},
                                                         ProjectionExpression="MasterIp")
                            except self.db_client.exceptions.ResourceNotFoundException:
                                r2 = None
                                return STATUS_OK
                            master_ip = r2['Item']['MasterIp']
                            callback_url = self.asg['EndPointUrl'] + "/callback/" + self.asg['AutoScaleGroupName']
                            data = {
                                  "status": "enable",
                                  "role": "slave",
                                  "master-ip": new_master_pip,
                                  "sync-interface": "port1",
                                  "psksecret": self.asg['AutoScaleGroupName'],
                                  "callback-url": callback_url
                            }
                            logger.info('posting auto-scale config: {}' .format(data))
                            self.api = FortiOSAPI()
                            self.api.login(existing_slave_eip, 'admin', self.asg['OrigMasterId'])
                            content = self.api.put(api='cmdb', path='system', name='auto-scale', data=data)
                            self.api.logout()
                            logger.info('restapi response: {}' .format(content))
        return STATUS_OK

    @staticmethod
    def get_aws_route_info(rtid, routes):
        subnet_id = None
        nic_id = None
        state = None
        cidr_block = None
        if 'RouteTables' in routes:
            for route in routes['RouteTables']:
                if 'RouteTableId' in route:
                    if route['RouteTableId'] != rtid:
                        continue
                if 'SubnetId' not in route['Associations'][0]:
                    continue
                subnet_id = route['Associations'][0]['SubnetId']
                if 'Routes' in route:
                    for r in route['Routes']:
                        if 'DestinationCidrBlock' in r and r['DestinationCidrBlock'] == '0.0.0.0/0':
                            cidr_block = r['DestinationCidrBlock']
                            if 'NetworkInterfaceId' in r:
                                nic_id = r['NetworkInterfaceId']
                                state = r['State']
        return {"RouteTableId": rtid, "SubnetId": subnet_id, "NetworkInterfaceId": nic_id,
                "DestinationCidrBlock": cidr_block, "State": state}

    def get_nic_status(self, nic):
        try:
            r = self.ec2_client.describe_network_interfaces(NetworkInterfaceIds=[nic])
        except ClientError as e:
            logger.exception('exception describe_network_interface():  %s' % e.Response)
            return False
        if 'NetworkInterfaces' in r and len(r['NetworkInterfaces']) > 0:
            if r['NetworkInterfaces'][0]['Status'] != 'in-use':
                return False
        return True

    def find_best_eni(self, subnet_id):
        nic = None
        if self.instance_id_tables is None:
            return None
        if len(self.instance_id_tables) > 0:
            for i in self.instance_id_tables:
                if i['PrivateSubnetId'] == subnet_id:
                    rc = self.get_nic_status(i['SecondENIId'])
                    if rc is True:
                        nic = i['SecondENIId']
                        break
                if nic is None:
                    rc = self.get_nic_status(i['SecondENIId'])
                    if rc is True:
                        nic = i['SecondENIId']
        return nic

    #
    # Brute forced and this code is so ugly.
    #
    # If route table is pointing to an IGW, find a fortigate in the same subnet and point the route to the internal ENI
    #   if you can't find a fortigate in the same subnet, look for a fortigate in the other AZ
    # If route table is point to an ENI and state = 'blackhole', this means the ENI doesn't exist anymore.
    #   so find a fortigate in the same subnet and point the route to the internal ENI
    #   if you can't find a fortigate in the same subnet, look for a fortigate in the other AZ
    #
    # TODO: what if gateway is a NAT Gateway? Don't think I have tested for that yet.
    #
    def verify_route_tables(self):
        if self.route_tables is None:
            return
        if len(self.route_tables) == 0:
            return
        for r in self.route_tables:
            rt_table_list = list([])
            rt_table_list.append(r['TypeId'])
            try:
                routes = self.ec2_client.describe_route_tables(RouteTableIds=rt_table_list)
            except ClientError as e:
                logger.exception('verify_route_table(): exception describe_route_tables() %s' % e)
                self.table.delete_item(Key={"Type": TYPE_ROUTETABLE_ID, "TypeId": r['TypeId']})
                continue
            for rtid in rt_table_list:
                aws_rt_info = self.get_aws_route_info(rtid, routes)
                for dbrt in self.route_tables:
                    if dbrt['Subnet'] == aws_rt_info['SubnetId']:
                        if 'NetworkInterfaceId' in dbrt:
                            db_eni = dbrt['NetworkInterfaceId']
                        else:
                            db_eni = None
                        eni_id = self.find_best_eni(aws_rt_info['SubnetId'])
                        if eni_id is None:
                            return
                        if aws_rt_info['NetworkInterfaceId'] is None:
                            db_eni = None
                        if db_eni != eni_id:
                            b3route = self.ec2_resource.Route(aws_rt_info['RouteTableId'],
                                                              aws_rt_info['DestinationCidrBlock'])
                            try:
                                b3route.replace(NetworkInterfaceId=eni_id)
                            except Exception as ex:
                                logger.exception('route.replace(): ex' % ex)
                                continue
                            r = RouteTable(self, aws_rt_info['SubnetId'])
                            r.eni = eni_id
                            r.route_table_id = rtid
                            r.write_to_db()
                            dbrt['NetworkInterfaceId'] = eni_id

    def callback_add_member_to_lb(self, ip, is_instance_master):
        if is_instance_master is True:
            logger.info("Adding MASTER to Load Balancer: ip = %s" % ip)
        else:
            logger.info("Adding SLAVE to Load Balancer: ip = %s" % ip)
        if self.table is not None:
            for db_instance in self.instance_id_tables:
                logger.debug('db_instanceID = {}' .format(db_instance))
                instance = db_instance['TypeId']
                db_instance_info = self.ec2_client.describe_instances(InstanceIds=[instance])
                db_instance_ip = db_instance_info['Reservations'][0]['Instances'][0]['PublicIpAddress']
                if ip == db_instance_ip or is_instance_master is True:
                    logger.info("describe target group: group = %s" % self.target_group)
                    if self.target_group is None:
                        tg = self.name
                    else:
                        tg = self.target_group
                    try:
                        lb_target_group = self.elbv2_client.describe_target_groups(Names=[tg])
                    except Exception as ex:
                        logger.exception('Exception, lb_target_group not found!: ex = %s' % ex)
                        return
                    if lb_target_group is not None and 'TargetGroups' in lb_target_group:
                        arn = lb_target_group['TargetGroups'][0]['TargetGroupArn']
                        name = lb_target_group['TargetGroups'][0]['TargetGroupName']
                        lbc = self.elbv2_client
                        if arn is not None:
                            t = {'Id': instance}
                            try:
                                add_member_to_lb = \
                                    lbc.register_targets(TargetGroupArn=arn, Targets=[t])
                            except Exception as ex:
                                logger.exception('EXCEPTION register_target(): id = %s, ex = %s' % (instance, ex))
                                return
                            if STATUS_OK == add_member_to_lb['ResponseMetadata']['HTTPStatusCode']:
                                logger.debug('  register instance {} to tgt grp: {}' .format(instance, name))
                            else:
                                logger.debug('FAIL to register {} to tgt grp: {}' .format(instance, name))
                            return
            logger.info('  Invalid IP for register_target(): {} !' .format(ip))

    def process_notification(self, data):
        if 'Message' not in data:
            return
        try:
            msg = json.loads(data['Message'])
        except ValueError:
            logger.exception('sns(): Notification Not Valid JSON: {}'.format(data['Message']))
            return HttpResponseBadRequest('Not Valid JSON')
        if 'Event' in msg and msg['Event'] == 'autoscaling:TEST_NOTIFICATION':
            logger.info('process_notification(): TEST_NOTIFICATION')
            return STATUS_OK
        if 'LifecycleTransition' in msg and msg['LifecycleTransition'] == 'autoscaling:EC2_INSTANCE_LAUNCHING':
            logger.info('process_notification(): LCH_LAUNCH - instance = %s' % msg['EC2InstanceId'])
            return self.lch_launch(data)
        if 'LifecycleTransition' in msg and msg['LifecycleTransition'] == 'autoscaling:EC2_INSTANCE_TERMINATING':
            logger.info('process_notification(): LCH_TERMINATE - instance = %s' % msg['EC2InstanceId'])
            return self.lch_terminate(data)
        if 'Event' in msg and msg['Event'] == 'autoscaling:EC2_INSTANCE_LAUNCH':
            logger.info('process_notification(): EC2_LAUNCH - instance = %s' % msg['EC2InstanceId'])
            return self.launch_instance(data)
        if 'Event' in msg and msg['Event'] == 'autoscaling:EC2_INSTANCE_TERMINATE':
            logger.info('process_notification(): EC2_TERMINATE - instance = %s' % msg['EC2InstanceId'])
            return self.terminate_instance(data)
