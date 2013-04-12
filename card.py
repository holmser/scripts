#!/usr/bin/env python

class Card:
	def __init__(self, rank, suit):
		self.rank = rank
		self.suit = suit
		self.ranks = [None, "ace", "2","3","4","5","6","7","8","9","10","Jack","Queen","King"]
		self.suits = {"s":"Spades", "d":"Diamonds","c":"Clubs","h":"Hearts"}

	def getRank(self):
		return self.rank

	def getSuit(self):
		return self.suit
	
	def __str__(self):
		return "%s of %s" % (self.ranks[self.rank], self.suits.get(self.suit))

