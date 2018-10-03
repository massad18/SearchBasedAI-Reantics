import random
import sys
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
        super(AIPlayer,self).__init__(inputPlayerId, "Vewy Greedy AI <(^w^<)")
        ## Initialize class variables on start of program ##

        self.foodCoords = []
        self.buildingCoords = []

        # Init depth limit for recursion
        self.depthLimit = 2

################################################################################

    # Evaluation function for the number of workers that the AI controls
    def evalWorkerCount(self, currentState, test = False, testvar = None):
        if test:
            workerCount = testvar
        else:
            workerCount = len(getAntList(currentState, currentState.whoseTurn, (WORKER,)))
        # Reward the AI for having only one worker
        if (workerCount > 1):
            return -1.0
        else:
            return workerCount

    # Evaluation function for the number of soldier that the AI controls
    def evalSoldierCount(self, currentState, test = False, testvar = None):
        if test:
            soldierCount = testvar
        else:
            soldierCount = len(getAntList(currentState, currentState.whoseTurn, (SOLDIER,)))
        # Reward for having more than 10 soldiers
        if (soldierCount > 10):
            return 1.0
        else:
            return 0.1 * soldierCount

    # Evaluation function for the difference in ants between AIs
    def evalAntDifference(self, currentState, test = False, testMyAnts = None, testEnemyAnts = None):
        if test:
            myAntCount = testMyAnts
            enemyAntCount = testEnemyAnts
        else:
            me = currentState.whoseTurn
            myAntCount = len(getAntList(currentState, me))
            enemyAntCount = len(getAntList(currentState, 1-me))
        # Evaluation score is the ratio of our AI's ants vs the total number of ants on the board
        return (myAntCount-enemyAntCount) / (myAntCount+enemyAntCount)

    # Evaluation function for the difference in health of the ants between AIs
    def evalHealthDifference(self, currentState, test = False, testMyAntList = None, testEnemyAntList = None):
        if test:
            myAnts = testMyAntList
            enemyAnts = testEnemyAntList
        else:
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

    # Evaluation function for the position of the worker
        # Rewards AI for collection food and bring the food back to the anthill/tunnel
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
                totalStepsToDestination += self.getMinStepsToTarget(worker.coords, self.buildingCoords)
            else:
                steps = self.getMinStepsToTarget(worker.coords, self.foodCoords)
                totalStepsToDestination += steps + MAX_STEPS_FROM_FOOD

        myInv = getCurrPlayerInventory(currentState)
        totalStepsToDestination += (11-myInv.foodCount) * 2 * MAX_STEPS_FROM_FOOD * len(workerList)
        scoreCeiling = 12 * 2 * MAX_STEPS_FROM_FOOD * len(workerList)
        evalScore = scoreCeiling - totalStepsToDestination
        # Max possible score is 1.0, where all workers are at their destination.
        return (evalScore/scoreCeiling)

    # Evaluation function for the position of the soldier
        # Rewards for being closer to enemy ants resulting in attack
    def evalSoldierPositions(self, currentState):
        me = currentState.whoseTurn
        soldierList = getAntList(currentState, me, (SOLDIER,))
        if (len(soldierList) == 0):
            return 0.0
        # Save the coordinates of all the enemy's ants.
        enemyAntCoords = self.getCoordsOfListElements(getAntList(currentState, 1-me))

        totalStepsToEnemy = 0
        for soldier in soldierList:
            totalStepsToEnemy += self.getMinStepsToTarget(soldier.coords, enemyAntCoords)

        # 30 steps is around the furthest distance one soldier could theoretically be
        # from an enemy ant. The actual step amounts should never be close to this number.
        MAX_STEPS_FROM_ENEMY = 30
        scoreCeiling = MAX_STEPS_FROM_ENEMY * len(soldierList)
        evalScore = scoreCeiling - totalStepsToEnemy
        # Max possible score is 1.0, where all soldiers are at their destination.
        return (evalScore/scoreCeiling)

    # Evaluation function for the position of the queen
        # Rewards AI for moving away from the closest enemy and not on the anthill/tunnel
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
            buildings = getConstrList(currentState, me, (ANTHILL, TUNNEL, FOOD))
            for building in buildings:
                if (queen.coords == building.coords):
                    return -1.0
            return totalDistance/scoreCeiling
        else:
            buildings = getConstrList(currentState, me, (ANTHILL, TUNNEL, FOOD))
            for building in buildings:
                if (queen.coords == building.coords):
                    return -1.0
            return 1.0

    # Helper function to get the minimum steps to the given target
    def getMinStepsToTarget(self, targetCoords, coordsList):
        minSteps = 10000 # infinity
        for coords in coordsList:
            stepsToTarget = approxDist(targetCoords, coords)
            if stepsToTarget < minSteps:
                minSteps = stepsToTarget
        return minSteps

    # Helper function to get the coordinate list of the given list
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
    #
    # Return:
    # A score between [-1.0, 1.0] such that + is good and - is bad for the
    #   player in question (me parameter)
    ##

    def evalOverall(self, currentState):
        # Determine if the game has ended and who won
        winResult = getWinner(currentState)
        if winResult == 1:
            return 1.0
        elif winResult == 0:
            return -1.0
        # else neither player has won this state.

        # Initialize the totalScore
        totalScore = 0

        # Initialize the weights for the specific evaluation functions
        workerCountWeight = 2
        soldierCountWeight = 3
        antDifferenceWeight = 1
        healthDifferenceWeight = 2
        workerPositionWeight = 1
        soldierPositionWeight = 1
        queenPositionWeight = 1
        totalWeight = 11

        # Determine evaluation scores multiplied by it weights
        totalScore += self.evalWorkerCount(currentState) * workerCountWeight
        totalScore += self.evalSoldierCount(currentState) * soldierCountWeight
        totalScore += self.evalAntDifference(currentState) * antDifferenceWeight
        totalScore += self.evalHealthDifference(currentState) * healthDifferenceWeight
        totalScore += self.evalWorkerPositions(currentState) * workerPositionWeight
        totalScore += self.evalSoldierPositions(currentState) * soldierPositionWeight
        totalScore += self.evalQueenPosition(currentState) * queenPositionWeight

        ### OVERALL WEIGHTED AVERAGE ###
        # Takes the weighted average of all of the scores
        # Only the game ending scores should be 1 or -1.
        overallScore = 0.99 * totalScore / totalWeight

        return overallScore

    # Recursion function to search for the best move per depth
    def greedyGetBestMove(self, currentState, currentDepth, parentNode):

        moves = listAllLegalMoves(currentState)

        possibleNodes = []
        for move in moves:
            resultState = getNextState(currentState, move)
            stateScore = self.evalOverall(resultState)
            possibleNodes.append(Node(resultState, move, stateScore, parentNode))

        # All possible nodes explored
        if (len(possibleNodes) == 0):
            return parentNode

        bestNode = self.nodeEvaluationHelper(possibleNodes)

        # Base case reached.
        if currentDepth >= self.depthLimit:
            return bestNode

        bestNode = self.greedyGetBestMove(bestNode.state, currentDepth+1, bestNode)
        return bestNode

    # Helper function that returns the child node of the given node
    def getChildNodes(self, parentNode):
        moves = listAllLegalMoves(parentNode.state)
        children = []
        for move in moves:
            resultState = getNextState(parentNode.state, move)
            stateScore = self.evalOverall(resultState, parentNode.state.whoseTurn)
            children.append(Node(resultState, move, stateScore, parentNode, parentNode.depth+1))
        return children

    # Helper function to determine the best score given  list of nodes
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
        # Acquire the location of the food and the buildings for the worker
        # position eval function
        self.foodCoords = self.getCoordsOfListElements(getConstrList(currentState, None, (FOOD,)))
        self.buildingCoords = self.getCoordsOfListElements(getConstrList(currentState, currentState.whoseTurn, (ANTHILL, TUNNEL)))

        # Run the recursive greedy best move function to determine the best move
        bestNode = self.greedyGetBestMove(currentState, 0, None)

        while not(bestNode.parent is None):
            bestNode = bestNode.parent
        return bestNode.move

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

# Node class that creates a new instance of a game state
# Takes in the game state, the move that was made to reach the state, the evaluation score of the state
# and the parent game state
class Node:

    def __init__(self, state, move, score, parent):
        self.state = state
        self.move = move
        self.score = score
        self.parent = parent


###########################################################################################################
##
# UNIT TESTS Cases
##

testAI = AIPlayer(0)
# evalWorkerCount
if testAI.evalWorkerCount(None,True,0) != 0:
    print("ERROR: Worker Count Evaluation1")
if testAI.evalWorkerCount(None,True,1) != 1:
    print("ERROR: Worker Count Evaluation2")
if testAI.evalWorkerCount(None,True,2) != -1:
    print("ERROR: Worker Count Evaluation3")

# evalSoldierCount
if testAI.evalSoldierCount(None,True,0) != 0:
    print("ERROR: Soldier Count Evaluation1")
if testAI.evalSoldierCount(None,True,5) != 0.5:
    print("ERROR: Soldier Count Evaluation2")
if testAI.evalSoldierCount(None,True,10) != 1:
    print("ERROR: Soldier Count Evaluation3")
if testAI.evalSoldierCount(None,True,12) != 1:
    print("ERROR: Soldier Count Evaluation4")

# evalAntDifference
if testAI.evalAntDifference(None,True,1,1) != 0:
    print("ERROR: Ant Difference Evaluation1")
if testAI.evalAntDifference(None,True,1,2) != -1/3:
    print("ERROR: Ant Difference Evaluation2")
if testAI.evalAntDifference(None,True,2,1) != 1/3:
    print("ERROR: Ant Difference Evaluation3")
if testAI.evalAntDifference(None,True,3,2) != .2:
    print("ERROR: Ant Difference Evaluation4")
if testAI.evalAntDifference(None,True,2,3) != -.2:
    print("ERROR: Ant Difference Evaluation5")

# evalHealthDifference
myAnts = [Ant((0,0), WORKER, 0), Ant((1,1), QUEEN, 0), Ant((2,2), DRONE, 0)]
enemyAnts = [Ant((9,9), WORKER, 1), Ant((8,8), SOLDIER, 1), Ant((7,7), R_SOLDIER, 1)]
if testAI.evalHealthDifference(None, True, myAnts, enemyAnts) != 4/28:
    print("ERROR: evalHealthDifference result")

# getMinStepsToTarget
if testAI.getMinStepsToTarget((0,0), [(2,2), (1,1), (3,3)]) != 2:
    print("ERROR: MinStepsToTarget result")

# getCoordsOfListElements
class testCoords:
    def __init__(self, c):
        self.coords = c

testCoordsList = [testCoords((0,1)), testCoords((1,2)), testCoords((45,2))]
if testAI.getCoordsOfListElements(testCoordsList) != [(0,1), (1,2), (45,2)]:
    print("ERROR: getCoordsOfListElements result")
