"""
Class to manage states for simple automation
"""
from machine import Timer
from time import localtime

SCHEDULER = {
    #  state : (t1, t2, ..., tn)   in minutes
    2: (0, 15, 30, 45),
    4: (1, 16, 31, 46),
    99: (9, 19, 29, 39, 49, 59)
}

class State:
    def __init__(self, initialState, delay=5000, defaultSate=None):
        """
        Usually only one object is created to manage the current state.
        :param initialState:
        :param callback: function to call back after a timer is set upon change of state
        :param delay: duration in seconds of the timer
        :param defaultSate: default state upon timer completion. If not indicated, initialState is used instead
        """
        self.lastState, self.currentState = -1, initialState
        self.defaultState = defaultSate or initialState
        self.firstTime = False  # change to True when changing state
        self.lastMinute = -1  # for scheduled tasks
        Timer(mode=Timer.PERIODIC, period=delay, callback=self.ontick)  # default every 5 seconds

    def changeToDefault(self, t=None):
        """
        Callback function to force the current state to the default state
        :return:
        """
        self.changeTo(self.defaultState)

    def changeTo(self, newState):
        """
        Change the currentState to a new given state, saving current in last State
        :param newState:
        :return:
        """
        self.lastState = self.currentState
        self.currentState = newState
        self.firstTime = True  # change to True when changing state for first time entry action
        # print("State changes from", self.lastState, "to", self.currentState)

    def ontick(self, timer):
        """
        Callback function for the scheduler ; needs to be called at least once a minute
        """
        curMinute = localtime()[4]
        if curMinute == self.lastMinute:
            print(".", end="")
            return  # already passed here
        else:
            print("|", end="")
            self.lastMinute = curMinute

        for state_idx, ticks in SCHEDULER.items():
            if curMinute in ticks:
                self.changeTo(state_idx)
                break

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

