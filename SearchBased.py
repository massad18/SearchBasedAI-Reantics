import random
import math
import sys
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *

from threading import Thread, BoundedSemaphore
import time

##
#AIPlayer
#Description: The responsbility of this class is to interact with the game by
#deciding a valid move based on a given game state. This class has methods that
#will be implemented by students in Dr. Nuxoll's AI course.
#
#Variables:
#   playerId - The id of the player.
##
class AIPlayer(Player):

    #__init__
    #Description: Creates a new Player
    #
    #Parameters:
    #   inputPlayerId - The id to give the new player (int)
    #   cpy           - whether the player is a copy (when playing itself)
    ##
    def __init__(self, inputPlayerId):
        super(AIPlayer,self).__init__(inputPlayerId, "Search Based Semaphore")
        ## Initialize class variables on start of program ##
        # Init weights for weighted average of evaluation function
        self.workerWeight = 2
        self.soldierWeight = 2
        self.allAntWeight = 1
        self.foodStoredDifferenceWeight = 1
        self.workerPositionsWeight = 1
        self.soldierPositionsWeight = 1
        self.queenPositionWeight = 1
        self.tempWeight = self.workerWeight

        # Init constants for y = Ce^(kx) equation s.t. x = [0,1] and y = [0,10]
            # y = [0,10] given that at 11, one team has 11 and the other has 0
            # used http://cs.jsu.edu/~leathrum/gwtmathlets/mathlets.php?name=expgraph
        self.foodStoredDifference_C_value = 0.05
        self.foodStoredDifference_k_value = 0.299573

        # Init depth limit for recursion
        self.depthLimit = 2

        # Set the max branches to recurse through
        self.max_branches = 1

        # Set the max number of locks for the semaphore
        self.max_lock = 10
        # If the maximum number of locks is greater than the maximum number of
        # branches, then make the max # locks equaled to the max # max_branches
            # Only need one thread per branch...
        if self.max_lock > self.max_branches:
            self.max_lock = self.max_branches

        self.gameTime = 0
        self.startTime = 0
        self.prevGameTime = 0
        self.bestTime = 0
        self.bestLock = 0

################################################################################
    ##
    # evalNumberAntType
    # Description: Evaluates the current gamestate for the given person
    #   and ant types. Will return a number between [-1.0, 1.0] where negative
    #   numbers are undesirable state for the given person and positive numbers
    #   are more desirable states. The more ants of the specific type that you have
    #   compared to the opponent yields higher output scores.
    #
    # Parameters:
    #   currentState - A clone of the current game state that will be evaluated
    #   me - A reference to the index of the player in question
    #   antType - A list of the types of ants that will be evaluated (all in upper case)
    #
    # Return:
    #   A score between [-1.0, 1.0] such that + is good and - is bad for the
    #   player in question (me parameter)
    ##
    def evalNumberAntType(self, currentState, me, antType):
        # Gather a list of my ants of the given type
        myAntCount = len(getAntList(currentState, me, antType))
        # Gather a list of the enemys ants of the given type
        enemyAntCount = len(getAntList(currentState, 1-me, antType))
        # Calculate the total number of ants of the given type
        sum = myAntCount+enemyAntCount

        # If antType is just Workers
        if len(antType) == 1 and antType[0] == WORKER:
            if myAntCount == 2:
                return 1.0
            elif myAntCount < 2:
                if sum == 0:
                    return 0.0
                else:
                    evalScore = (myAntCount-enemyAntCount)/sum
                    return evalScore
            else:
                self.tempWeight = self.workerWeight
                self.workerWeight = 1000
                return -1.0
        # Assuming we are looking at all other ants except the queen
        elif len(antType) == 4:
            if len(getAntList(currentState, me, [DRONE, ])) > 0:
                self.tempWeight = self.allAntWeight
                self.allAntWeight = 10
                return -1.0
            elif len(getAntList(currentState, me, [R_SOLDIER, ])) > 0:
                self.tempWeight = self.allAntWeight
                self.allAntWeight = 10
                return -1.0


        if sum == 0:
            return 0.0
        else:
            evalScore = (myAntCount-enemyAntCount)/sum
            return evalScore

 ##
    # evalNumberFoodStored
    # Description: Evaluates the current gamestate for the given person
    #   and the amount of food that they have stored. Will return a number between
    #   [-1.0, 1.0] where negative numbers are undesirable state for the given
    #   person and positive numbers are more desirable states. The more food that
    #   the player has stored, compared to their enemy, the higher the score returned.
    #
    # Parameters:
    #   currentState - A clone of the current game state that will be evaluated
    #
    # Return:
    #   A score between [-1.0, 1.0] such that + is good and - is bad for the
    #   player in question (me parameter)
    ##
    def evalNumberFoodStoredDifference(self, currentState, me):
        myInv = currentState.inventories[me]
        enemyInv = currentState.inventories[1-me]
        # Gather the number of food the AI has stored
        myFoodCount = myInv.foodCount
        # Gather the number of food the enemy has stored
        enemyFoodCount = enemyInv.foodCount

        # Calculate the total food gathered
        sum = myFoodCount+enemyFoodCount

        if sum == 0:
            return 0.0
        # If the AIs food is greater than the enemys...
            # Have the difference be positive and the final score be positive
        elif myFoodCount > enemyFoodCount:
            difference = myFoodCount - enemyFoodCount
            evalScore = self.foodStoredDifference_C_value*math.exp(self.foodStoredDifference_k_value*difference)
            return evalScore
        # If the AIs food is less than the enemys...
            # Have the difference be positive and the final score be negative
        else:
            difference = enemyFoodCount - myFoodCount
            evalScore = self.foodStoredDifference_C_value*math.exp(self.foodStoredDifference_k_value*difference)
            return -evalScore

    def evalWorkerPositions(self, currentState):
        me = currentState.whoseTurn
        workerList = getAntList(currentState, me, (WORKER,))
        if (len(workerList) == 0):
            return 0.0

        # Save the coordinates of each food on the board.
        foodCoords = self.getCoordsOfListElements(getConstrList(currentState, None, (FOOD,)))

        # Save the coordinates of my food receiving buildings.
        buildingCoords = self.getCoordsOfListElements(getConstrList(currentState, me, (ANTHILL, TUNNEL)))

        # 16 steps is around the furthest distance one worker could theoretically be
        # from a food source. The actual step amounts should never be close to this number.
        MAX_STEPS_FROM_FOOD = 16

        # Calculate the total steps each worker is from its nearest destination.
        totalStepsToDestination = 0
        for worker in workerList:
            if worker.carrying:
                totalStepsToDestination += self.getMinStepsToTarget(currentState, worker.coords, buildingCoords)
            else:
                steps = self.getMinStepsToTarget(currentState, worker.coords, foodCoords)
                totalStepsToDestination += steps + MAX_STEPS_FROM_FOOD

        myInv = getCurrPlayerInventory(currentState)
        totalStepsToDestination += (11-myInv.foodCount) * 2 * MAX_STEPS_FROM_FOOD * len(workerList)
        scoreCeiling = 12 * 2 * MAX_STEPS_FROM_FOOD * len(workerList)
        evalScore = scoreCeiling - totalStepsToDestination
        # Max possible score is 1.0, where all workers are at their destination.
        return (evalScore/scoreCeiling)

    def evalSoldierPositions(self, currentState):
        me = currentState.whoseTurn
        soldierList = getAntList(currentState, me, (SOLDIER,))
        if (len(soldierList) == 0):
            return 0.0
        # Save the coordinates of all the enemy's ants.
        #enemyAntCoords = self.getCoordsOfListElements(getAntList(currentState, 1-me))
        enemyQueenCoords = getEnemyInv(None, currentState).getQueen().coords

        totalStepsToEnemy = 0
        for soldier in soldierList:
            #totalStepsToEnemy += self.getMinStepsToTarget(currentState, soldier.coords, enemyAntCoords)
            totalStepsToEnemy += stepsToReach(currentState, soldier.coords, enemyQueenCoords)

        # 30 steps is around the furthest distance one soldier could theoretically be
        # from an enemy ant. The actual step amounts should never be close to this number.
        MAX_STEPS_FROM_ENEMY = 30
        scoreCeiling = MAX_STEPS_FROM_ENEMY * len(soldierList)
        evalScore = scoreCeiling - totalStepsToEnemy
        # Max possible score is 1.0, where all soldiers are at their destination.
        return (evalScore/scoreCeiling)

    def evalQueenPosition(self, currentState):
        return 0.0

    def getMinStepsToTarget(self, currentState, targetCoords, coordsList):
        minSteps = 10000 # infinity
        for coords in coordsList:
            stepsToTarget = stepsToReach(currentState, targetCoords, coords)
            if stepsToTarget < minSteps:
                minSteps = stepsToTarget
        return minSteps

    def getCoordsOfListElements(self, elementList):
        coordList = []
        for element in elementList:
            coordList.append(element.coords)
        return coordList

    ##
    # evalOverall
    # Description: Calls all of the evaluation scores and multiplies them by a
    #   weight. This allows the AI to fine tune the evaluation scores to better
    #   suit favorable moves and strategies.
    #
    # Parameters:
    #   currentState - A clone of the current game state that will be evaluated
    #   me - A reference to the index of the player in question
    #
    # Return:
    # A score between [-1.0, 1.0] such that + is good and - is bad for the
    #   player in question (me parameter)
    ##

    def evalOverall(self, currentState, me):
        winResult = getWinner(currentState)
        if winResult == 1:
            return 1.0
        elif winResult == 0:
            return -1.0
        # else neither player has won this state.

        ### EVALUATE THE RATIO OF ANTS ###
        allScores = []
        weightsum = 0
        # Evaluate the ratio of the AIs worker ants to the enemys worker ants
        workerScore = self.evalNumberAntType(currentState, me, [WORKER, ]) * self.workerWeight
        allScores.append(workerScore)
        weightsum += self.workerWeight

        self.workerWeight = self.tempWeight

        # Evaluate the ratio of the AIs sodlier ants to the enemys soldier ants
        soldierScore = self.evalNumberAntType(currentState, me, [SOLDIER, ]) * self.soldierWeight
        allScores.append(soldierScore)
        weightsum += self.soldierWeight

        # Evaluate the ratio of the AIs ants to the enemys ants (excluding the queen)
        allAntScore = self.evalNumberAntType(currentState, me, [WORKER, SOLDIER, DRONE, R_SOLDIER, ]) * self.allAntWeight
        allScores.append(allAntScore)
        weightsum += self.allAntWeight

        self.allAntWeight = self.tempWeight

        ### EVALUATE THE RATIO OF FOOD STORED ###
        # Evaluate the ratio of the AIs food count to the enemys food count
        foodStoredDifferenceScore = self.evalNumberFoodStoredDifference(currentState, me) * self.foodStoredDifferenceWeight
        allScores.append(foodStoredDifferenceScore)
        weightsum += self.foodStoredDifferenceWeight

        ### EVALUATE THE POSITIONS OF OUR ANTS ###
        workerPositionScore = self.evalWorkerPositions(currentState) * self.workerPositionsWeight
        allScores.append(workerPositionScore)
        weightsum += self.workerPositionsWeight

        soldierPositionScore = self.evalSoldierPositions(currentState) * self.soldierPositionsWeight
        allScores.append(soldierPositionScore)
        weightsum += self.soldierPositionsWeight

        ### OVERALL WEIGHTED AVERAGE ###
        # Takes the weighted average of all of the scores
        # Only the game ending scores should be 1 or -1.
        overallScore = 0.99 * sum(allScores)/weightsum

        #print("Ratio of Worker Ants: " + str(workerScore))
        #print("Ratio of Solider Ants: " + str(soldierScore))
        #print("Ratio of Total Ants (excluding Queen): " + str(allAntScore))
        #print("Ratio of Food Stored: " + str(foodStoredScore))
        #print("Worker Position Score:" + str(workerPositionScore))
        #print("Soldier Position Score:" + str(soldierPositionScore))
        #print("Overall Score: " + str(overallScore))

        #print()

        return overallScore

    # Secondary helper function for the thread
        # Exactly the same as the other recursive calls, except that at the end
        # of the recursive call, release the lock that it held from the semaphore
    def threadHelper(self, semaphore, childList, currentState, currentDepth, parentNode):
        childList.append(self.recursiveEval(currentState, currentDepth+1, parentNode))
        semaphore.release()

    def recursiveEval(self, currentState, currentDepth, parentNode):
        #Useful pointers
        myInv = getCurrPlayerInventory(currentState)
        me = currentState.whoseTurn

        moves = listAllLegalMoves(currentState)

        # start = time.time()

        possibleNodes = []
        lowestNode = None

        for move in moves:
            resultState = getNextState(currentState, move)
            stateScore = self.evalOverall(resultState, me)
            # Prune the possible nodes that will be checked by considering only
            # the top "self.max_branches" scoring nodes
            if len(possibleNodes) == 0:
                lowestNode = Node(resultState, move, stateScore, parentNode)
                possibleNodes.append(lowestNode)
            elif len(possibleNodes) >= self.max_branches:
                if stateScore > lowestNode.score:
                    possibleNodes.remove(lowestNode)
                    lowestNode = Node(resultState, move, stateScore, parentNode)
                    possibleNodes.append(lowestNode)
                    for node in possibleNodes:
                        if node.score < lowestNode.score:
                            lowestNode = node
            else:
                possibleNodes.append(Node(resultState, move, stateScore, parentNode))

        # end = time.time()
        #
        # print("Time Elapsed: " + str(end-start))

        # Base case reached.
        if currentDepth >= self.depthLimit:
            bestNode = self.nodeEvaluationHelper(possibleNodes)
            return bestNode

        # Only create threads at the top level
            # Prevents recursively creating threads
        if currentDepth == 0:
            threads = []
            semaphore = BoundedSemaphore(self.max_lock)

        currentChildNodes = []
        for node in possibleNodes:
            # At the top level only... create a thread that will create a recursive call
            if currentDepth == 0:
                # Try to acquire a lock from the semaphore
                semaphore.acquire()
                # Create the thread for the given branch of the tree
                t = Thread(target=self.threadHelper, args=(semaphore, currentChildNodes, node.state, currentDepth+1, node))
                # Add the thread to a list to later join them together
                threads.append(t)
                # Start the individual thread
                t.start()
            # If not the top of the branch, continue recursive calls normally
            # on the same thread
            else:
                currentChildNodes.append(self.recursiveEval(node.state, currentDepth+1, node))

        # If the recursive calls have finished and are back to the top of the branch...
            # Join all of the threads together to continue to the next step
        if currentDepth == 0:
            for t in threads:
                if t.isAlive():
                    t.join()

        if len(currentChildNodes) == 0:
            return parentNode
        bestNode = self.nodeEvaluationHelper(currentChildNodes)
        return bestNode

    def nodeEvaluationHelper(self, nodeList):
        maxScore = -100000 # negative infinity
        bestNode = None
        for node in nodeList:
            if (node.score > maxScore):
                bestNode = node
                maxScore = node.score
        return bestNode

################################################################################

    ##
    #getPlacement
    #
    #Description: called during setup phase for each Construction that
    #   must be placed by the player.  These items are: 1 Anthill on
    #   the player's side; 1 tunnel on player's side; 9 grass on the
    #   player's side; and 2 food on the enemy's side.
    #
    #Parameters:
    #   construction - the Construction to be placed.
    #   currentState - the state of the game at this point in time.
    #
    #Return: The coordinates of where the construction is to be placed
    ##
    def getPlacement(self, currentState):
        # Initialize class variables on start of game

        self.gameTime = 0
        self.startTime = time.time()

        numToPlace = 0
        #implemented by students to return their next move
        if currentState.phase == SETUP_PHASE_1:    #stuff on my side
            numToPlace = 11
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on your side of the board
                    y = random.randint(0, 3)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        elif currentState.phase == SETUP_PHASE_2:   #stuff on foe's side
            numToPlace = 2
            moves = []
            for i in range(0, numToPlace):
                move = None
                while move == None:
                    #Choose any x location
                    x = random.randint(0, 9)
                    #Choose any y location on enemy side of the board
                    y = random.randint(6, 9)
                    #Set the move if this space is empty
                    if currentState.board[x][y].constr == None and (x, y) not in moves:
                        move = (x, y)
                        #Just need to make the space non-empty. So I threw whatever I felt like in there.
                        currentState.board[x][y].constr == True
                moves.append(move)
            return moves
        else:
            return [(0, 0)]

    ##
    #getMove
    #Description: Gets the next move from the Player.
    #
    #Parameters:
    #   currentState - The state of the current game waiting for the player's move (GameState)
    #
    #Return: The Move to be made
    ##
    def getMove(self, currentState):

        # print("############## Get Move ###############")
        #
        # start = time.time()

        bestNode = self.recursiveEval(currentState, 0, None)
        goalNode = bestNode
        while not(goalNode.parent is None):
            goalNode = bestNode.parent

        # end = time.time()
        # print("RECURSION: " + str(end-start))

        return goalNode.move

    ##
    #getAttack
    #Description: Gets the attack to be made from the Player
    #
    #Parameters:
    #   currentState - A clone of the current state (GameState)
    #   attackingAnt - The ant currently making the attack (Ant)
    #   enemyLocation - The Locations of the Enemies that can be attacked (Location[])
    ##
    def getAttack(self, currentState, attackingAnt, enemyLocations):
        #Attack a random enemy.
        return enemyLocations[random.randint(0, len(enemyLocations) - 1)]

    ##
    #registerWin
    #
    # This agent doens't learn
    #
    def registerWin(self, hasWon):
        self.gameTime = time.time() - self.startTime


        # print("Previous Time: " + str(self.prevGameTime) + " Current Game Time: " + str(self.gameTime))
        # print("Old Max_Lock: " + str(self.max_lock))
        #
        # if self.gameTime < 120:
        #     if self.gameTime < self.bestTime:
        #         self.bestTime = self.gameTime
        #         self.bestLock = self.max_lock
        #     print("++++++++++++ 2 MINUTES ++++++++++++")
        #     print(self.max_lock)
        #     print("+++++++++++++++++++++++++++++++++++")
        #
        # if (self.prevGameTime - self.gameTime) < 30:
        #     self.max_lock -= 1
        #     self.prevGameTime = self.gameTime
        # elif self.gameTime > self.prevGameTime:
        #     self.max_lock += 2
        #
        # print("New Max Lock: " + str(self.max_lock))
        # print("BEST MAX LOCK: " + str(self.bestLock))
        # print("###############################################################")
        # print()

    def evalNumAnts(self, currentState):
        pass

class Node:

    def __init__(self, state, move, score, parent):
        self.state = state
        self.move = move
        self.score = score
        self.parent = parent
