class Channel:
    """
    ThingSpeak channel identification object
    """

    def __init__(self, name, apiKey):
        self.name = name
        self.apiKey = apiKey

    def __hash__(self):
        return hash((self.name, self.apiKey))

    def __str__(self):
        return "<{0}[{1}]>".format(self.name, self.apiKey)

    def __repr__(self):
        return self.__str__()
