class AuthAPIError(Exception):
    pass


class AuthAPINetworkError(AuthAPIError):
    pass


class AuthAPITimeout(AuthAPIError):
    pass


class AuthAPIUnexpectedStatusCode(AuthAPIError):

    def __init__(self, status_code, json):
        message = 'Status: {0}.\nJson: {1}'.format(status_code, json)
        self.status_code = status_code
        self.json = json
        super().__init__(message)


class EmailNotConfirmedError(AuthAPIError):
    pass
