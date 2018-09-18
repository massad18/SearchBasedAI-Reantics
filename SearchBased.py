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
# evalNumberAntType
# Description:
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
def evalNumberAntType(currentState, me, antType):
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
# evalNumberFood
# Description:
#
# Parameters:
#   currentState - A clone of the current game state that will be evaluated
# Return:
#   A score between [-1.0, 1.0] such that + is good and - is bad for the
#   player in question (me parameter)
##
def evalNumberFood(currentState, me):
    myInv = getCurrPlayerInventory(currentState)
    enemyInv = currentState.inventories[1-me]
    # Gather the number of food the AI has stored
    myFoodCount = myInv.foodCount
    # Gather the number of food the enemy has stored
    enemyFoodCount = enemyInv.foodCount

    # Calculate the total food gathered
    sum = myFoodCount+enemyFoodCount

    if sum == 0:
        return 0.0
    else:
        evalScore = (myFoodCount-enemyFoodCount)/sum
        return evalScore

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
        # Initialize class variables on start of program

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

        # Evaluate the ratio of the AIs worker ants to the enemys worker ants
        print("Ratio of Worker Ants: " + str(evalNumberAntType(currentState, me, [WORKER, ])))
        # Evaluate the ratio of the AIs sodlier ants to the enemys soldier ants
        print("Ratio of Solider Ants: " + str(evalNumberAntType(currentState, me, [SOLDIER, ])))
        # Evaluate the ratio of the AIs ants to the enemys ants (excluding the queen)
        print("Ratio of Total Ants (excluding Queen): " + str(evalNumberAntType(currentState, me, [WORKER, SOLDIER, DRONE, R_SOLDIER, ])))
        # Evaluate the ratio of the AIs food count to the enemys food count
        print("Ratio of Food Count: " + str(evalNumberFood(currentState, me)))
        print()
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
