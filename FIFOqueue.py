# Refer to https://github.com/dm03514/python-algorithms/tree/main/pyalgorithms/queues
class Node:
    def __init__(self, value, _next=None):
        self.value = value
        self._next = _next


class FIFOQueue():
    """
    FIFOQueue provides a linked list implementation.

    Operation Runtimes:
    - enqueue: 0(1)
    - dequeue: 0(1)
    - peek: 0(1)
    - size: 0(1)
    """
    def __init__(self):
        self._head = None
        self._tail = None
        self._size = 0

    def enqueue(self, item):
        if self._size == 0:
            # if the queue is empty, initialize both head and tail to the item
            node = Node(value=item)
            self._tail = self._head = node
        else:
            # append the item at the end of the queue i.e. put the item in line (FIFO)
            self._tail._next = Node(value=item)
            self._tail = self._tail._next
        # always increment size
        self._size += 1

    def dequeue(self):
        if self._size == 0:
            return None
        # get the current head i.e. the FIRST in
        node = self._head
        # set the head to the next in line
        self._head = self._head._next
        self._size -= 1
        if self._size == 0:
            # set the tail to empty
            self._tail = None
        # return the first value
        return node.value

    def peek(self):
        if self._size == 0:
            return None
        return self._head.value
    
    def __len__(self):
        return self._size
    
    def __bool__(self):
        return self._size > 0

