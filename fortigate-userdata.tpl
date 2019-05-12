#config-version=FGTAWS-6.0.4-FW-build0231-190107:opmode=0:vdom=0:user=admin
#conf_file_ver=353991204618736
#buildno=0231
#global_vdom=1
config system global
	set pre-login-banner disable
end
config system admin
    edit "admin"
	set force-password-change disable
        set password Password123!
    next
end
