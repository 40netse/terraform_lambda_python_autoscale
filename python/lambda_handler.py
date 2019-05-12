import json
import const
import urllib3


def handler(event, context):
    """Endpoint that SNS accesses. Includes logic verifying request"""
    # print("Fortigate Autoscale Received context: %s", context)
    # print("Fortigate Autoscale Received event: " + json.dumps(event, indent=2))
    print("=====")
    print("body: " + body + "type: " + json.dumps(t, indent=2))
    if isinstance(event['body'], str):
        # requests return str in python 2.7
        request_body = event['body']
    try:
        data = json.loads(request_body)
    except ValueError:
        const.logger.exception('sns(): Notification Not Valid JSON: {}'.format(request_body))
        return HttpResponseBadRequest('Not Valid JSON')
    const.logger.debug("sns(): request = %s" % (json.dumps(request_body, sort_keys=True, indent=4, separators=(',', ': '))))

    if 'TopicArn' not in data:
        return HttpResponseBadRequest('Not Valid JSON')
    url = None
    if 'HTTP_HOST' in request.META:
        url = 'https://' + request.META['HTTP_HOST']

    #
    # Handle Subscription Request up front. The first Subscription request will trigger a DynamoDB table creation
    # and it will not be responded to. The second request will have an ACTIVE table and the subscription request
    # will be responded to and start the flow of Autoscale Messages.
    #
    if request.method == 'POST' and data['Type'] == 'SubscriptionConfirmation':
        const.logger.info('SubscriptionConfirmation()')
        g = AutoScaleGroup(data)
        const.logger.debug('SubscriptionConfirmation 1(): g = %s' % g)
        #
        # Create the master table if it does not exist. Master table is just a list of autoscale group names.
        # The master table is named "fortinet_autoscale_<region>_<account_id>.
        # The scheduled cloudwatch process will read the master table every 60 seconds and execute
        # all the housekeeping functions for each managed autoscale group.
        #
        master_table_found = False
        master_table_name = "fortinet_autoscale_" + g.region + "_" + g.account
        try:
            t = g.db_client.describe_table(TableName=master_table_name)
            if 'ResponseMetadata' in t:
                if t['ResponseMetadata']['HTTPStatusCode'] == const.STATUS_OK:
                    master_table_found = True
        except g.db_client.exceptions.ResourceNotFoundException:
            master_table_found = False
        if master_table_found is False:
            try:
                g.db_client.create_table(AttributeDefinitions=const.attribute_definitions,
                                            TableName=master_table_name, KeySchema=const.schema,
                                            ProvisionedThroughput=const.provisioned_throughput)
            except Exception, ex:
                const.logger.debug('SubscriptionConfirmation master_table_create(): table_status = %s' % ex)
                return
        mt = g.db_resource.Table(master_table_name)
        asg = {"Type": const.TYPE_AUTOSCALE_GROUP, "TypeId": g.name}
        master_table_written = False
        while master_table_written is False:
            try:
                mt.put_item(Item=asg)
                master_table_written = True
            except g.db_client.exceptions.ResourceNotFoundException:
                master_table_written = False
                time.sleep(5)
        #
        # End of master table
        #
        r = None
        try:
            r = g.db_client.describe_table(TableName=g.name)
        except Exception, ex:
            table_status = 'NOTFOUND'

        if r is not None and 'Table' in r:
            table_status = r['Table']['TableStatus']

        const.logger.debug('SubscriptionConfirmation 2(): table_status = %s' % table_status)
        #
        # If NOTFOUND, fall through to write_to_db() and it will create the table
        #
        if table_status == 'NOTFOUND':
            pass
        #
        # If ACTIVE and we received a new Subscription Confirmation, delete everything in the table and start over
        #
        elif table_status == 'ACTIVE':
            table = g.db_resource.Table(g.name)
            response = table.scan()
            if 'Items' in response:
                for r in response['Items']:
                    table.delete_item(Key={"Type": r['Type'], "TypeId": r['TypeId']})
        #
        # If CREATING, this is the second Subscription Confirmation and AWS is still busy creating the table
        #   just ignore this request
        elif table_status == 'CREATING':
            return
        else:
            #
            # Unknown status. 404
            #
            raise Http404

        const.logger.debug('SubscriptionConfirmation pre write_to_db()')
        g.write_to_db(data, url)

        const.logger.debug('SubscriptionConfirmation post write_to_db(): g.status = %s' % g.status)
        if g.status == 'CREATING':
            return
        if g.asg is None:
            raise Http404

        if g.status == 'ACTIVE':
            const.logger.info('SubscriptionConfirmation respond_to_subscription request()')
            return respond_to_subscription_request(request)
