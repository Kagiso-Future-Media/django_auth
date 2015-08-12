class CASException(Exception):

    def __init__(self, status_code, json):
        message = 'Status: {0}.\nJson: {1}'.format(status_code, json)
        self.status_code = status_code
        self.json = json
        super().__init__(message)
