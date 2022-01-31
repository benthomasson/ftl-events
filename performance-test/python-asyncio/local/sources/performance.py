
import json

def main(queue, args):

    for i in range(int(args['limit'])):
        queue.put(dict(text='hello'))
