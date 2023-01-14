"""
Class to manage states for simple automation
"""
from machine import Timer
class State:
    def __init__(self, initialState, delay=None, defaultSate=None):
        """
        Usually only one object is created to manage the current state.
        :param initialState:
        :param callback: function to call back after a timer is set upon change of state
        :param delay: duration in seconds of the timer
        :param defaultSate: default state upon timer completion. If not indicated, initialState is used instead
        """
        self.lastState, self.currentState = -1, initialState
        self.delay = delay
        self.defaultState = defaultSate or initialState
        self.firstTime = False  # change to True when changing state

    def changeToDefault(self, t=None):
        """
        Callback function to force the current state to the default state
        :return:
        """
        self.lastState = self.currentState
        self.currentState = self.defaultState

    def changeTo(self, newState):
        """
        Change t\the currentState to a new given state, saving current in last State
        :param newState:
        :return:
        """
        self.lastState = self.currentState
        self.currentState = newState
        self.firstTime = True  # change to True when changing state for first time entry action
        if self.delay and self.currentState != self.defaultState:
            Timer(period=self.delay * 1000, mode=Timer.ONE_SHOT, callback=self.changeToDefault)

    def __str__(self):
        return(f"currentState:{self.currentState} /  lastState={self.lastState}")

if __name__ == "__main__":
    from time import sleep
    state = State(99, delay=5)
    print(state==99)
    state.changeTo(0)
    print(state)
    state.changeTo(10)
    sleep(6)
    print(state)

