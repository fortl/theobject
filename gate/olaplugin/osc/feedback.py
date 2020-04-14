class Feedback:
    def __init__(self, *messages):
        self.messages = list(messages)
    
    def add_message(self, message):
        self.messages.append(message)

    def add(self, feedback):
        self.messages.extend(feedback.messages)
        return self
    
    def prefix(self, prefix):
        for message in self.messages:
            message['address'] = prefix + message['address']
        return self 
