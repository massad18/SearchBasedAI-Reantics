import random
import sys
import math
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

        # Init constants for y = Ce^(kx) equation s.t. x = [0,1] and y = [0,10]
            # y = [0,10] given that at 11, one team has 11 and the other has 0
            # used http://cs.jsu.edu/~leathrum/gwtmathlets/mathlets.php?name=expgraph
        self.foodStoredDifference_C_value = 0.05
        self.foodStoredDifference_k_value = 0.299573

        # Init depth limit for recursion
        self.depthLimit = 1

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

        if myAntCount+enemyAntCount == 0:
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

        # If I am the winner, return 1.0
        if getWinner(currentState) == me:
            return 1.0
        # If the enemy is the winner, return -1.0
        elif getWinner(currentState) == 1-me:
            return -1.0

        ### EVALUATE THE RATIO OF ANTS ###
        # Evaluate the ratio of the AIs worker ants to the enemys worker ants
        workerScore = self.evalNumberAntType(currentState, me, [WORKER, ]) * self.workerWeight
        print("Ratio of Worker Ants: " + str(workerScore))
        # Evaluate the ratio of the AIs sodlier ants to the enemys soldier ants
        soldierScore = self.evalNumberAntType(currentState, me, [SOLDIER, ]) * self.soldierWeight
        print("Ratio of Solider Ants: " + str(soldierScore))
        # Evaluate the ratio of the AIs ants to the enemys ants (excluding the queen)
        allAntScore = self.evalNumberAntType(currentState, me, [WORKER, SOLDIER, DRONE, R_SOLDIER, ]) * self.allAntWeight
        print("Ratio of Total Ants (excluding Queen): " + str(allAntScore))

        ### EVALUATE THE RATIO OF THE DIFFERENCE IN FOOD STORED ###
        # Evaluate the ratio of the AIs food count to the enemys food count
        foodStoredDifferenceScore = self.evalNumberFoodStoredDifference(currentState, me) * self.foodStoredDifferenceWeight
        print("Ratio of Food Stored: " + str(foodStoredDifferenceScore))

        ### OVERALL WEIGHTED AVERAGE ###
        # Sum up all of the weights for the weighted average
        totalWeight = self.workerWeight + self.soldierWeight + self.allAntWeight + self.foodStoredDifferenceWeight
        # Takes the weighted average of all of the scores
        overallScore = (workerScore + soldierScore + allAntScore + foodStoredDifferenceScore)/totalWeight
        print("Overall Score: " + str(overallScore))

        print()

        return overallScore

################################################################################

    ##
    # createGameStateNode
    # Description: Called when a new GameState node is to be added to the list
    #   of nodes. It documents the move that is to be made, the GameState that
    #   will result in the move, the evaluation score of that state, and the
    #   parent GameState. By default, the keyword parameters are set to None and
    #   can be changed by direct reference to their name or in order of position
    #
    # Parameters:
    #   nodeList - A complete list of all of the nodes up to that point
    #
    # Keyword Parameters:
    #   Move = None - The Move that would be taken in the given state from the
    #       parent node
    #   Child = None - The state that would be reached by taking that move
    #   Score = None - The evaluation score of the proposed state (Child GameState)
    #   Parent = None - A reference to the parent GameState
    #
    ##
    def createGameStateNode(self, nodeList, Move = None, Child = None, Score = None, Parent = None):

        nodeList.append({
            "Move": Move,
            "Child": Child,
            "Score": Score,
            "Parent": Parent
        })

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
        #Useful pointers
        myInv = getCurrPlayerInventory(currentState)
        me = currentState.whoseTurn

        moves = listAllLegalMoves(currentState)
        selectedMove = moves[random.randint(0,len(moves) - 1)];

        #don't do a build move if there are already 3+ ants
        numAnts = len(currentState.inventories[currentState.whoseTurn].ants)
        while (selectedMove.moveType == BUILD and numAnts >= 3):
            selectedMove = moves[random.randint(0,len(moves) - 1)];

        #
        self.evalOverall(currentState, me)

        return selectedMove

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
