class CASError(Exception):
    pass


class CASNetworkError(CASError):
    pass


class CASTimeout(CASError):
    pass


class CASUnexpectedStatusCode(CASError):

    def __init__(self, status_code, json):
        message = 'Status: {0}.\nJson: {1}'.format(status_code, json)
        self.status_code = status_code
        self.json = json
        super().__init__(message)


class EmailNotConfirmedError(CASError):
    pass
