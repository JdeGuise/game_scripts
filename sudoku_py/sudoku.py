import argparse
from Tkinter import Tk, Canvas, Frame, Button, BOTH, TOP, BOTTOM

# available difficulties / boards
BOARDS = ['debug', 'n00b', 'l33t', 'error']
MARGIN = 20
SIDE = 50
WIDTH = HEIGHT = MARGIN * 2 + SIDE * 9  # WIDTH AND HEIGHT OF THE WHOLE BOARD

class SudokuError(Exception):
	"""
	An application specific error
	"""
	pass

def parse_arguments():
	"""
	Parses arguments of the form:
		sudoku.py <board name>
	Where 'board name' must be in the  'BOARD' list
	"""

	# create Argument Parser object
	arg_parser = argparse.ArgumentParser()

	# add argument for --board to require the board to be in the BOARDS list
	arg_parser.add_argument("--board",
							help="Desired board name",
							type=str,
							choices=BOARDS,
							required=True)

	# create a dictionary of keys = argument flags, and value = argument
	args = vars(arg_parser.parse_args())
	return args['board']

class SudokuUI(Frame):
	"""
	The Tkinter UI, responsible for drawing the board and accepting user input
	"""

	def __init__(self, parent, game):
		self.game = game
		self.parent = parent

		Frame.__init__(self, parent)

		self.row, self.col = 0, 0

		self.__initUI()

	# "main" for our UI
	def __initUI(self):
		self.parent.title("Sudoku")
		self.pack(fill=BOTH, expand=1)
		self.canvas = Canvas(self,
							width=WIDTH,
							height=HEIGHT)
		self.canvas.pack(fill=BOTH, side=TOP)
		clear_button = Button(self,
							text="Clear answers",
							command=self.__clear_answers)
		clear_button.pack(fill=BOTH, side=BOTTOM)

		self.__draw_grid()
		self.__draw_puzzle()

		self.canvas.bind("<Button-1>", self.__cell_clicked)
		self.canvas.bind("<Key>", self.__key_pressed)

	# grid drawing helper method
	def __draw_grid(self):
		"""
			Draws grid divided with blue lines into 3x3 squares
		"""
		for i in xrange(10):
			color = "blue" if i % 3 == 0 else "gray"

			x0 = MARGIN + i * SIDE
			y0 = MARGIN
			x1 = MARGIN + i * SIDE
			y1 = HEIGHT - MARGIN
			self.canvas.create_line(x0, y0, x1, y1, fill=color)

			x0 = MARGIN
			y0 = MARGIN + i * SIDE
			x1 = WIDTH - MARGIN
			y1 = MARGIN + i * SIDE
			self.canvas.create_line(x0, y0, x1, y1, fill=color)

	# board drawing helper method
	def __draw_puzzle(self):
		# automatically clears puzzle (helps for start-overs)
		self.canvas.delete("numbers")

		for i in xrange(9):
			for j in xrange(9):
				# grab our square's answer from our puzzle in SudokuGame.puzzle
				answer = self.game.puzzle[i][j]

				if answer != 0:
					x = MARGIN + j * SIDE + SIDE / 2
					y = MARGIN + i * SIDE + SIDE / 2
					original = self.game.start_puzzle[i][j]
					color = "black" if answer == original else "sea green"
					self.canvas.create_text(
						x, y, text=answer, tags="numbers", fill=color
					)

	# clear answers from board
	def __clear_answers(self):
		self.game.start()
		self.canvas.delete("victory")
		self.__draw_puzzle()

	# callback for cell clicking
	def __cell_clicked(self, event):
		# stop clicks on the board if the game is over
		if self.game.game_over:
			return

		x, y = event.x, event.y

		# if click was w/in margin of our puzzle boundaries, set the canvas focus
		if (MARGIN < x < WIDTH - MARGIN and MARGIN < y < HEIGHT - MARGIN):
			self.canvas.focus_set()

		# get row and col numbers from x, y coordinates
		row, col = (y - MARGIN) / SIDE, (x - MARGIN) / SIDE

		# if cell was selected already, deselect on click
		if (row, col) == (self.row, self.col):
			self.row, self.col = -1, -1
		elif self.game.puzzle[row][col] == 0:
			self.row, self.col = row, col

		self.__draw_cursor()

	# draw our "highlight" box
	def __draw_cursor(self):
		# clearing out previously highlighted cell
		self.canvas.delete("cursor")

		# as long as we're clicking within the game itself
		if self.row >= 0 and self.col >= 0:
			x0 = MARGIN + self.col * SIDE + 1
			y0 = MARGIN + self.row * SIDE + 1
			x1 = MARGIN + (self.col + 1) * SIDE - 1
			y1 = MARGIN + (self.row + 1) * SIDE - 1

			# draw the highlight rectangle
			self.canvas.create_rectangle(
				x0, y0, x1, y1,
				outline="red", tags="cursor"
			)

	# callback for key presses
	def __key_pressed(self, event):
		# if game is over, don't register key presses
		if self.game.game_over:
			return

		# if our active row and column are within the game board, and 
		# the button that was pressed is a single digit
		if self.col >= 0 and self.row >= 0 and event.char in "1234567890":
			# the value at that grid space is now set to player input
			self.game.puzzle[self.row][self.col] = int(event.char)
			
			# set cursor to the corner
			self.col, self.row = -1, -1

			# redraw the puzzle
			self.__draw_puzzle()

			# redraw the cursor
			self.__draw_cursor()

			# check for win condition, if found, draw_victory()
			if self.game.check_win():
				self.__draw_victory()

	# draw victory helper method
	def __draw_victory():
		# create an oval (initialized as a circle)
		x0 = y0 = MARGIN + SIDE * 2
		x1 = y1 = MARGIN + SIDE * 7

		# create actual oval object
		self.canvas.create_oval(
			x0, y0, x1, y1,
			tags="victory", fill="dark orange", outline="black"
		)

		# add text to oval object
		x = y = MARGIN + 4 * SIDE + SIDE / 2
		self.canvas.create_text(
			x, y,
			text="You win!", tags="winner",
			fill="white", font=("Arial", 32)
		)	

class SudokuBoard(object):
	"""
		Sudoku Board Representation
	"""
	def __init__(self, board_file):
		self.board = self.__create_board(board_file)

	def __create_board(self, board_file):
		# create initial matrix
		board = []

		# iterate over each line
		for line in board_file:
			line = line.strip()

			#raise error if line !9 characters
			if len(line) != 9:
				board = []
				raise SudokuError(
					"Each line in the sudoku puzzle must be 9 chars long"
				)

			# create a list for the line
			board.append([])

			# iterate over each character
			for charac in line:
				# raise error if character != int
				if not charac.isdigit():
					raise SudokuError(
						"Each set of characters in the sudoku puzzle must be within 0-9"
					)

				# Add to the latest list for the line
				board[-1].append(int(charac))

		# raise error if !9 lines
		if len(board) != 9:
			raise SudokuError("Error: length of board must be 9")

		# return constructed board
		return board

class SudokuGame(object):
	"""
		A Sudoku Game Object, in charge of:
		 1. storing board state, and 
		 2. checking for puzzle completion
	"""

	def __init__(self, board_file):
		self.board_file = board_file
		# keep a static copy of our started puzzle for comparison
		self.start_puzzle = SudokuBoard(board_file).board

	def start(self):
		self.game_over = False
		self.puzzle = []

		# for our x coordinate in array from 0..8
		for i in xrange(9):
			#build fresh empty matrix
			self.puzzle.append([])
			for j in xrange(9):
				self.puzzle[i].append(self.start_puzzle[i][j])

	def check_win(self):
		for row in xrange(9):
			if not self.__check_row(row):
				return False
		for column in xrange(9):
			if not self.__check_column(column):
				return False
		for row in xrange(3):
			for column in xrange(3):
				if not self.__check_square(row, column):
					return False
		self.game_over = True
		return True

	def __check_block(self, block):
		return set(block) == set(range(1, 10))

	def __check_row(self, row):
		return self.__check_block(self.puzzle[row])

	def __check_col(self, col):
		return self.__check_block([self.puzzle[row][column] for row in xrange(9)])

	def __check_sqr(self, sqr):
		return self.__check_block(
			[
				self.puzzle[r][c]
				for r in xrange(row * 3, (row + 1) * 3)
				for c in xrange(col * 3, (col + 1) * 3)
			]
		)


if __name__ == '__main__':
	board_name = parse_arguments()

	# opening our board file
	with open('%s.sudoku' % board_name, 'r') as boards_file:
		# creating our game object for the board file
		game = SudokuGame(boards_file)
		game.start()

		# setting the root of the Tk canvas
		root = Tk()

		# creating the SudokuUI based on the root canvas object and game
		SudokuUI(root, game)

		root.geometry("%dx%d" % (WIDTH, HEIGHT + 40))

		# start the program mainloop
		root.mainloop()
