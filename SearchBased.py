import random
import math
import sys
import time
from multiprocessing.dummy import Pool as ThreadPool
sys.path.append("..")  #so other modules can be found in parent dir
from Player import *
from Constants import *
from Construction import CONSTR_STATS
from Ant import UNIT_STATS
from Move import Move
from GameState import *
from AIPlayerUtils import *

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
        super(AIPlayer,self).__init__(inputPlayerId, "Search Based 0.1")
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

        self.foodCoords = []
        self.buildingCoords = []

        # Init depth limit for recursion
        self.depthLimit = 2

        self.moves = []

        self.resetTime()

    def resetTime(self):
        self.workerCounting = 0
        self.soldierCounting = 0
        self.antDifference = 0
        self.healthDifference = 0
        self.countingSteps = 0
        self.wPosTime = 0
        self.sPosTime = 0

        self.listMoves = 0
        self.evalStates = 0
        self.findBestNode = 0

    def printTimes(self):
        print("=============== Timing =======================")
        """
        print("Worker Counting:   " + str(self.workerCounting))
        print("Soldier Counting:  " + str(self.soldierCounting))
        print("Ant Difference:    " + str(self.antDifference))
        print("Health Difference: " + str(self.healthDifference))
        print("Counting Steps:    " + str(self.countingSteps))
        print("Worker Position:   " + str(self.wPosTime))
        print("Soldier Position:  " + str(self.sPosTime))
        print()
        """
        print("Listing Moves:     " + str(self.listMoves))
        print("Eval States:       " + str(self.evalStates))
        print("Finding Best Node: " + str(self.findBestNode))

        total = self.workerCounting + self.soldierCounting + self.antDifference + self.healthDifference + self.wPosTime + self.sPosTime
        print("======= Eval Time: " + str(total))
        print()

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

    def evalWorkerCount(self, currentState):
        workerCount = len(getAntList(currentState, currentState.whoseTurn, (WORKER,)))
        if (workerCount > 2):
            return -1.0
        else:
            return 0.25 * workerCount

    def evalSoldierCount(self, currentState):
        soldierCount = len(getAntList(currentState, currentState.whoseTurn, (SOLDIER,)))
        if (soldierCount > 10):
            return 1.0
        else:
            return 0.1 * soldierCount

    def evalAntDifference(self, currentState):
        me = currentState.whoseTurn
        myAntCount = len(getAntList(currentState, me))
        enemyAntCount = len(getAntList(currentState, 1-me))
        return (myAntCount-enemyAntCount) / (myAntCount+enemyAntCount)

    def evalHealthDifference(self, currentState):
        me = currentState.whoseTurn
        myAnts = getAntList(currentState, me)
        enemyAnts = getAntList(currentState, 1-me)
        myTotalHealth = 0
        enemyTotalHealth = 0
        for ant in myAnts:
            myTotalHealth += ant.health
        for ant in enemyAnts:
            enemyTotalHealth += ant.health
        return (myTotalHealth-enemyTotalHealth) / (myTotalHealth+enemyTotalHealth)

    def evalWorkerPositions(self, currentState):
        me = currentState.whoseTurn
        workerList = getAntList(currentState, me, (WORKER,))
        if (len(workerList) == 0):
            return -1.0

        # 16 steps is around the furthest distance one worker could theoretically be
        # from a food source. The actual step amounts should never be close to this number.
        MAX_STEPS_FROM_FOOD = 16

        # Calculate the total steps each worker is from its nearest destination.
        totalStepsToDestination = 0
        for worker in workerList:
            if worker.carrying:
                totalStepsToDestination += self.getMinStepsToTarget(currentState, worker.coords, self.buildingCoords)
            else:
                steps = self.getMinStepsToTarget(currentState, worker.coords, self.foodCoords)
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
        enemyAntCoords = self.getCoordsOfListElements(getAntList(currentState, 1-me))
        #enemyQueenCoords = getEnemyInv(None, currentState).getQueen().coords

        totalStepsToEnemy = 0
        for soldier in soldierList:
            #totalStepsToEnemy += self.getMinStepsToTarget(currentState, soldier.coords, enemyAntCoords)
            totalStepsToEnemy += approxDist(soldier.coords, enemyQueenCoords)

        # 30 steps is around the furthest distance one soldier could theoretically be
        # from an enemy ant. The actual step amounts should never be close to this number.
        MAX_STEPS_FROM_ENEMY = 30
        scoreCeiling = MAX_STEPS_FROM_ENEMY * len(soldierList)
        evalScore = scoreCeiling - totalStepsToEnemy
        # Max possible score is 1.0, where all soldiers are at their destination.
        return (evalScore/scoreCeiling)

    def evalQueenPosition(self, currentState):
        me = currentState.whoseTurn
        queen = getCurrPlayerQueen(currentState)
        enemyAnts = getAntList(currentState, 1-me, (DRONE, SOLDIER, R_SOLDIER))
        enemyAntCoords = self.getCoordsOfListElements(enemyAnts)
        totalDistance = 0
        for enemyCoords in enemyAntCoords:
            totalDistance += approxDist(queen.coords, enemyCoords)

        if (len(enemyAntCoords) > 0):
            MAX_STEPS_FROM_ENEMY = 30
            scoreCeiling = MAX_STEPS_FROM_ENEMY * len(enemyAntCoords)
            return totalDistance/scoreCeiling
        else:
            buildings = getConstrList(currentState, me, (ANTHILL, TUNNEL, FOOD))
            for building in buildings:
                if (queen.coords == building.coords):
                    return -1.0
            return 1.0

    def getMinStepsToTarget(self, currentState, targetCoords, coordsList):
        minSteps = 10000 # infinity
        for coords in coordsList:
            #stepsToTarget = stepsToReach(currentState, targetCoords, coords)
            stepsToTarget = approxDist(targetCoords, coords)
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
        """
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
        """

        totalScore = 0

        workerCountWeight = 2
        soldierCountWeight = 3
        antDifferenceWeight = 1
        healthDifferenceWeight = 2
        workerPositionWeight = 1
        soldierPositionWeight = 1
        queenPositionWeight = 1
        totalWeight = 12

        timeStart = time.clock()
        totalScore += self.evalWorkerCount(currentState) * workerCountWeight
        self.workerCounting += time.clock() - timeStart

        timeStart = time.clock()
        totalScore += self.evalSoldierCount(currentState) * soldierCountWeight
        self.soldierCounting += time.clock() - timeStart

        timeStart = time.clock()
        totalScore += self.evalAntDifference(currentState) * antDifferenceWeight
        self.antDifference += time.clock() - timeStart

        timeStart = time.clock()
        totalScore += self.evalHealthDifference(currentState) * healthDifferenceWeight
        self.healthDifference += time.clock() - timeStart

        timeStart = time.clock()
        totalScore += self.evalWorkerPositions(currentState) * workerPositionWeight
        self.wPosTime += time.clock() - timeStart

        timeStart = time.clock()
        totalScore += self.evalSoldierPositions(currentState) * soldierPositionWeight
        self.sPosTime += time.clock() - timeStart

        totalScore += self.evalQueenPosition(currentState) * queenPositionWeight

        ### OVERALL WEIGHTED AVERAGE ###
        # Takes the weighted average of all of the scores
        # Only the game ending scores should be 1 or -1.
        overallScore = 0.9 * totalScore / totalWeight
        #overallScore = 0.99 * sum(allScores)/weightsum

        #print()

        return overallScore

    def greedyGetBestMove(self, currentState, currentDepth, parentNode):
        #Useful pointers
        myInv = getCurrPlayerInventory(currentState)
        me = currentState.whoseTurn

        moves = listAllLegalMoves(currentState)

        possibleNodes = []
        for move in moves:
            resultState = getNextState(currentState, move)
            stateScore = self.evalOverall(resultState, me)
            possibleNodes.append(Node(resultState, move, stateScore, parentNode))

        if (len(possibleNodes) == 0):
            return parentNode

        bestNode = self.nodeEvaluationHelper(possibleNodes)
        # Base case reached.
        if currentDepth >= self.depthLimit:
            return bestNode

        bestNode = self.greedyGetBestMove(bestNode.state, currentDepth+1, bestNode)
        return bestNode

    def recursiveEvalOld(self, currentState, currentDepth, parentNode):
        #Useful pointers
        myInv = getCurrPlayerInventory(currentState)
        me = currentState.whoseTurn

        t = time.clock()
        moves = listAllLegalMoves(currentState)
        self.listMoves += time.clock() - t

        t = time.clock()
        possibleNodes = []
        for move in moves:
            resultState = getNextState(currentState, move)
            stateScore = self.evalOverall(resultState, me)
            possibleNodes.append(Node(resultState, move, stateScore, parentNode))
        self.evalStates += time.clock() - t

        # Base case reached.
        if currentDepth >= self.depthLimit:
            bestNode = self.nodeEvaluationHelper(possibleNodes)
            return bestNode

        currentChildNodes = []
        for node in possibleNodes:
            currentChildNodes.append(self.recursiveEval(node.state, currentDepth+1, node))
        if len(currentChildNodes) == 0:
            return parentNode
        bestNode = self.nodeEvaluationHelper(currentChildNodes)
        return bestNode

    def recursiveEval(self, currentState, currentDepth):
        moves = listAllLegalMoves(currentState)
        possibleNodes = []
        for move in moves:
            possibleNodes.append(Node(getNextState(currentState, move), move, 0, None))

        # Base case reached.
        if currentDepth >= self.depthLimit:
            bestScore = -100000 # negative infinity
            for node in possibleNodes:
                score = self.evalOverall(node.state, currentState.whoseTurn)
                if (score > bestScore):
                    bestScore = score
            return bestScore

        for node in possibleNodes:
            node.score = self.recursiveEval(node.state, currentDepth+1)
        bestNode = self.nodeEvaluationHelper(possibleNodes)
        if (currentDepth == 0):
            return bestNode.move
        else:
            return bestNode.score

    def getChildNodes(self, parentNode):
        moves = listAllLegalMoves(parentNode.state)
        children = []
        for move in moves:
            resultState = getNextState(parentNode.state, move)
            stateScore = self.evalOverall(resultState, parentNode.state.whoseTurn)
            children.append(Node(resultState, move, stateScore, parentNode, parentNode.depth+1))
        return children

    def nodeEvaluationHelper(self, nodeList):
        t = time.clock()
        maxScore = -100000 # negative infinity
        bestNode = None
        for node in nodeList:
            if (node.score > maxScore):
                bestNode = node
                maxScore = node.score
        self.findBestNode += time.clock() - t
        return bestNode

    def threadFunction(self, node):
        return self.recursiveEval(node.state, 1, node)

    # Experimental, probably not good.
    def setupMoveSearch(self, currentState):
        moves = listAllLegalMoves(currentState)
        possibleNodes = []
        for move in moves:
            resultState = getNextState(currentState, move)
            stateScore = self.evalOverall(resultState, currentState.whoseTurn)
            possibleNodes.append(Node(resultState, move, stateScore, None))
        #possibleNodesHalf1 = possibleNodes[:len(possibleNodes)//2]
        #possibleNodesHalf2 = possibleNodes[len(possibleNodes)//2:]

        pool = ThreadPool(4)
        nextNodes = pool.map(self.threadFunction, possibleNodes)
        bestNode = self.nodeEvaluationHelper(nextNodes)
        pool.close()
        pool.join()
        return bestNode.move

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
        self.foodCoords = self.getCoordsOfListElements(getConstrList(currentState, None, (FOOD,)))
        self.buildingCoords = self.getCoordsOfListElements(getConstrList(currentState, currentState.whoseTurn, (ANTHILL, TUNNEL)))

        """
        if (len(self.moves) > 0):
            nextMove = self.moves.pop()
            return nextMove
        bestNode = self.recursiveEvalOld(currentState, 0, None)
        while not(bestNode.parent is None):
            self.moves.append(bestNode.move)
            bestNode = bestNode.parent
        return bestNode.move
        """

        #return self.setupMoveSearch(currentState)
        return self.recursiveEval(currentState, 0)

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
        #method templaste, not implemented
        pass

    def evalNumAnts(self, currentState):
        pass

class Node:

    def __init__(self, state, move, score, parent, depth = -1):
        self.state = state
        self.move = move
        self.score = score
        self.parent = parent
        self.depth = depth

    # Used for Node compatibility with heap data structure.
    def __lt__(self, otherNode):
        return self.score < otherNode.score
