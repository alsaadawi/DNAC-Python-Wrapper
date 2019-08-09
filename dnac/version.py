
from dnac import DnacError, \
                 SUPPORTED_DNAC_VERSIONS, \
                 UNSUPPORTED_DNAC_VERSION
from dnac.dnacapi import DnacApi, \
                         DnacApiError
from dnac.crud import OK, \
                      REQUEST_NOT_OK, \
                      ERROR_MSGS
from dnac.file import File
from dnac.task import Task

MODULE = 'version.py'

VERSION_RESOURCE_PATH = {
    '1.2.10': '/api/v1/archive-config/network-device',
    '1.3.0.2': '/api/v1/archive-config/network-device',
    '1.3.0.3': '/api/v1/archive-config/network-device'
}

VERSION_SUB_RESOURCE_PATH = {
    '1.2.10': '/version',
    '1.3.0.2': '/version',
    '1.3.0.3': '/version'
}

CONFIG_FILE_SUB_RESOURCE_PATH = {
    '1.2.10': '/file',
    '1.3.0.2': '/file',
    '1.3.0.3': '/file'
}

RUNNING_CONFIG = 'RUNNINGCONFIG'
STARTUP_CONFIG = 'STARTUPCONFIG'

CONFIG_FILE_TYPES = [
    RUNNING_CONFIG,
    STARTUP_CONFIG
]

ILLEGAL_CONFIG_FILE_TYPE = 'Illegal config file type'
NO_SYNC = ''
NO_CONFIG = {}
VERSION_DELETE_FAILED = 'Version deletion failed'


class Version(DnacApi):

    def __init__(self,
                 dnac,
                 device_id,
                 version_id,
                 verify=False,
                 timeout=5):

        if dnac.version in SUPPORTED_DNAC_VERSIONS:
            path = '%s/%s%s/%s' % (VERSION_RESOURCE_PATH[dnac.version],
                                  device_id,
                                  VERSION_SUB_RESOURCE_PATH[dnac.version],
                                  version_id)
        else:
            raise DnacError('__init__: %s: %s' % (UNSUPPORTED_DNAC_VERSION, dnac.version))
        self.__id = version_id
        self.__device_id = device_id
        self.__config_files = {}  # key = fileType, value = File object
        name = 'version_%s' % self.__id
        super(Version, self).__init__(dnac,
                                      name,
                                      resource=path,
                                      verify=verify,
                                      timeout=timeout)
        # load the version
        url = self.dnac.url + self.resource
        version, status = self.crud.get(url,
                                        headers=self.dnac.hdrs,
                                        verify=self.verify,
                                        timeout=self.timeout)
        if status != OK:
            raise DnacApiError(
                MODULE, '__init__', REQUEST_NOT_OK, url, OK, status, ERROR_MSGS[status], str(version)
                              )
        self.__created_time = version['versions'][0]['createdTime']
        self.__sync_status = version['versions'][0]['startupRunningStatus']
        for file in version['versions'][0]['files']:
            # iterate through all the archive's versions and load the config files
            if file['fileType'] not in CONFIG_FILE_TYPES:
                    raise DnacApiError(
                        MODULE, '__init__', ILLEGAL_CONFIG_FILE_TYPE, '',
                        str(CONFIG_FILE_TYPES), '', file['fileType'], ''
                                      )
            config_file = File(dnac, file['fileId'])
            config_file.get_results(is_json=False)
            self.__config_files[file['fileType']] = config_file

# end __init__()

    @property
    def id(self):
        return self.__id

# end id getter

    @property
    def device_id(self):
        return self.__device_id

# end device_id getter

    @property
    def created_time(self):
        return self.__created_time

# end created_time getter

    @property
    def sync_status(self):
        return self.__sync_status

# end sync_status getter

    @property
    def config_files(self):
        return self.__config_files

# end config_files getter

    def delete(self):
        url = self.dnac.url + self.resource
        results, status = self.crud.delete(url, headers=self.dnac.hdrs)
        if status != OK:
            raise DnacApiError(MODULE, 'delete', REQUEST_NOT_OK, url, OK, status, ERROR_MSGS[status], '')
        task = Task(self.dnac, results['response']['taskId'])
        task.get_task_results()
        if task.is_error:
            raise DnacApiError(MODULE, 'delete', task.progress, '', '', '', task.failure_reason, '')
        else:
            del self.dnac.api[self.name]

# end delete()

    def delete_config_file(self, file_id):
        url = '%s%s/%s/%s' % (self.dnac.url, self.resource, CONFIG_FILE_SUB_RESOURCE_PATH[self.dnac.version], file_id)
        results, status = self.crud.delete(url, headers=self.dnac.hdrs)
        if status != OK:
            raise DnacApiError(MODULE, 'delete_config', REQUEST_NOT_OK, url, OK, status, ERROR_MSGS[status], '')
        task = Task(self.dnac, results['response']['taskId'])
        task.get_task_results()
        if task.is_error:
            raise DnacApiError(MODULE, 'delete_config', task.progress, '', '', '', task.failure_reason, '')
        else:
            for config_file_type, config_file in self.__config_files.items():
                if file_id == config_file.id:
                    del self.__config_files[config_file_type]
                    break
            del self.dnac.api['file_%s' % file_id]

# end delete_config_file

# end class Version

# begin unit test


if __name__ == '__main__':

    from dnac import Dnac

    d = Dnac()

    dev_id = '84e4b133-2668-4705-8163-5694c84e78fb'
    ver_id = 'f5a320d7-3cd5-463d-967e-a49a4b83c33f'

    v = Version(d, dev_id, ver_id)

    print('Version:')
    print()

    print('  id = ', v.id)
    print('  created_time = ', v.created_time)
    print('  sync_status = ', v.sync_status)
    print('  config_files = ', v.config_files)
    print('  type(config_files) = ', str(type(v.config_files)))
    print()

    print('Version: printing config files associated with the version:')
    print()

    print('  startup config:')
    print(v.config_files[STARTUP_CONFIG].results)
    print()
    print('  running config:')
    print(v.config_files[RUNNING_CONFIG].results)
    print()

    print('Version: unit test complete')