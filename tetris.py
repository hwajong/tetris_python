#!/usr/bin/python
# -*- coding: utf-8 -*-

from Tkinter import *
from random import randint
import tkMessageBox
import sys
import time
import os.path

scale=20 # 테크노미노의 각 블록 크기
max_x=10 # 보드판 x 사이즈
max_y=22 # 보드판 y 사이즈
offset=5 # 보드판 여백
direction_coord = { "left": (-1,0), "right": (1,0), "down": (0,1) }

# 왼쪽 상황판 
class InfoBoard():
	def __init__(self, tk):
		self.canvas = Canvas(tk, width=100, height=(max_y*scale)+offset, bg="cornsilk", bd=0)
		self.canvas.pack(side=LEFT)
		self.preview_id = []
		self.remained_text_id = 0
		self.stage_text_id = 0

	def draw_next_tetromino(self, tetromino):
		for id in self.preview_id:
			self.canvas.delete(id)
		for coord in tetromino.coords:
			#print "coords (%d %d)" % coord
			(x,y) = coord
			x -= 2
			y += 1
			rx = (x * scale/2)
			ry = (y * scale/2)
			id = self.canvas.create_rectangle(rx, ry, rx+scale/2, ry+scale/2, fill=tetromino.color)
			self.preview_id.append(id)

	def draw_remained_text(self, nremained):
		self.canvas.delete(self.remained_text_id)
		self.remained_text_id = self.canvas.create_text(45, max_y*scale-5, text="Remained: %-d" % nremained)

	def draw_stage_text(self, nstage):
		self.canvas.delete(self.stage_text_id)
		self.stage_text_id = self.canvas.create_text(30, max_y*scale-30, text="Stage: %-d" % nstage)


# 게임보드 
class GameBoard():
	def __init__(self, tk):

		self.landed = {}
		self.mission_block_set = set()
		self.tk = tk

		self.canvas = Canvas(tk, height=(max_y * scale) + offset, width=(max_x * scale) + offset, bd=0)
		self.canvas.pack()

	def clear(self):
		self.landed.clear()
		self.mission_block_set.clear()
		self.canvas.delete("all")

	def check_block(self, (x,y)):
		if x < 0 or x >= max_x or y < 0 or y >= max_y:
			return False
		elif self.landed.has_key((x,y)):
			return False
		else:
			return True

	def add_block(self, (x,y), color):
		rx = (x * scale) + offset
		ry = (y * scale) + offset

		return self.canvas.create_rectangle(rx, ry, rx+scale, ry+scale, fill=color)

	def add_mission_block(self, (x,y)):
		rx = (x * scale) + offset
		ry = (y * scale) + offset

		id = self.canvas.create_rectangle(rx, ry, rx+scale, ry+scale, fill="Gray80", outline="red")
		self.landed[(x,y)] = id
		self.mission_block_set.add(id)

	def get_mission_block_num(self):
		return len(self.mission_block_set)

	def move_block(self, id, coord):
		x, y = coord
		self.canvas.move(id, x*scale, y*scale)

	def delete_block(self, id):
		self.canvas.delete(id)
	
	def check_for_complete_row(self, shape):
		for block in shape.blocks:
			self.landed[ block.coord() ] = block.id

		# find the first not empty row
		not_empty_row = 0
		for y in xrange(0, max_y-1, 1):
			row_is_not_empty = False
			for x in xrange(max_x):
				if self.landed.get((x,y), None):
					row_is_not_empty = True
					break;

			if row_is_not_empty:
				not_empty_row = y
				break

		# Now scan up and until a complete row is found.
		rows_deleted = 0
		y = max_y - 1
		while y > not_empty_row:
			complete_row = True
			for x in xrange(max_x):
				if self.landed.get((x,y), None) is None:
					complete_row = False
					break;

			if complete_row:
				rows_deleted += 1

				#delete the completed row
				#print "y = %d" % y
				#print "not_empty_row = %d" % not_empty_row
				for x in xrange(max_x):
					block_id = self.landed.pop((x,y))
					self.delete_block(block_id)
					if block_id in self.mission_block_set:
						self.mission_block_set.remove(block_id)
					del block_id

				# move all the rows above it down
				for ay in xrange(y-1, not_empty_row-1, -1):
					#print "ay = %d" % ay
					for x in xrange(max_x):
						block = self.landed.get((x,ay), None)
						if block:
							block = self.landed.pop((x,ay))
							dx,dy = direction_coord["down"]
							self.move_block(block, direction_coord["down"])

							self.landed[(x+dx, ay+dy)] = block

				# move the empty row down index down too
				not_empty_row +=1

			else:
				y -= 1

		return rows_deleted

# 테크노미노를 구성하는 블록 정의
class Block(object):
	def __init__(self, id, (x,y)):
		self.id = id
		self.x, self.y = (x,y)

	def coord(self):
		return (self.x, self.y)

class Tetromino(object):
	@classmethod
	def check_and_create(self, game_board, coords, color):
		for coord in coords:
			if not game_board.check_block(coord):
				return None

		return self(game_board, coords, color)

	def __init__(self, game_board, coords, color):
		self.game_board = game_board
		self.blocks = []

		for coord in coords:
			block = Block(self.game_board.add_block(coord, color), coord)
			self.blocks.append(block)

	# 테크노미노를 보드에서 이동시킨다. 
	def move(self, direction):
		d_x, d_y = direction_coord[direction]

		for block in self.blocks:
			x = block.x + d_x
			y = block.y + d_y

			if not self.game_board.check_block((x,y)):
				return False

		for block in self.blocks:
			block.x = block.x + d_x
			block.y = block.y + d_y
			self.game_board.move_block(block.id, (d_x, d_y))

		return True

	# 테크노미노 시계방향 90도 회전
	def rotate(self):
		middle = self.blocks[1]

		rel = []
		for block in self.blocks:
			rel.append( (block.x-middle.x, block.y-middle.y ) ) 

		# to rotate 90-degrees (x,y) = (-y, x)
		# First check that the there are no collisions or out of bounds moves.
		for idx in xrange(len(self.blocks)):
			rel_x, rel_y = rel[idx]
			x = middle.x+rel_y
			y = middle.y-rel_x

			if not self.game_board.check_block( (x, y) ):
				return False

		for idx in xrange(len(self.blocks)):
			rel_x, rel_y = rel[idx]
			x = middle.x+rel_y
			y = middle.y-rel_x

			diff_x = x - self.blocks[idx].x
			diff_y = y - self.blocks[idx].y

			self.game_board.move_block( self.blocks[idx].id, (diff_x, diff_y) )

			self.blocks[idx].x = x 
			self.blocks[idx].y = y 

		return True


class Tetromino_O(Tetromino):
	coords = [(4,0),(5,0),(4,1),(5,1)]
	color = "Yellow"
	@classmethod
	def create(self, game_board):
		return super(Tetromino_O, self).check_and_create(game_board, self.coords, self.color)

	def rotate(self):
		pass

class Tetromino_T(Tetromino):
	coords = [(3,1),(4,1),(5,1),(4,0)]
	color = "BlueViolet"
	@classmethod
	def create(self, game_board):
		return super(Tetromino_T, self).check_and_create(game_board, self.coords, self.color)

class Tetromino_Z(Tetromino):
	coords = [(3,0),(4,0),(4,1),(5,1)]
	color = "DarkRed"
	@classmethod
	def create(self, game_board):
		return super(Tetromino_Z, self).check_and_create(game_board, self.coords, self.color)

class Tetromino_S(Tetromino):
	coords = [(3,1),(4,1),(4,0),(5,0)]
	color = "LimeGreen"
	@classmethod
	def create(self, game_board):
		return super(Tetromino_S, self).check_and_create(game_board, self.coords, self.color)

class Tetromino_L(Tetromino):
	coords = [(3,0),(3,1),(4,1),(5,1)]
	color = "MediumBlue"
	@classmethod
	def create(self, game_board):
		return super(Tetromino_L, self).check_and_create(game_board, self.coords, self.color)

class Tetromino_J(Tetromino):
	coords = [(3,1),(4,1),(5,1),(5,0)]
	color = "DarkOrange"
	@classmethod
	def create(self, game_board):
		return super(Tetromino_J, self).check_and_create(game_board, self.coords, self.color)

class Tetromino_I(Tetromino):
	coords = [(3,0),(4,0),(5,0),(6,0)]
	color = "Cyan"
	@classmethod
	def create(self, game_board):
		return super(Tetromino_I, self).check_and_create(game_board, self.coords, self.color)


class Tetris(object):
	def __init__(self):
		self.tk = Tk()
		self.tk.geometry('+600+400')
		self.tk.title("테트리스")

		self.info_board = InfoBoard(self.tk)
		self.stage = 1

		self.game_board = GameBoard(self.tk)
		self.tetrominoes = [Tetromino_O, Tetromino_T, Tetromino_Z, Tetromino_S, Tetromino_L, Tetromino_J, Tetromino_I]

		# 키다운 콜백함수 등록 
		self.tk.bind("<Left>",  self.callback_left)
		self.tk.bind("<Right>", self.callback_right)
		self.tk.bind("<Down>",  self.callback_down)
		self.tk.bind("<space>", self.callback_space)
		self.tk.bind("<Up>",    self.callback_rotate)
		self.tk.bind("p",       self.callback_pass_stage)

		self.cur_tetromino = None
		self.next_tetromino_class = None
		self.load_stage()

	# 스테이지 데이타 파일 로딩
	def load_stage(self):
		stage_file = "stage%d.dat" % self.stage

		if not os.path.exists(stage_file):
			return False

		f = open(stage_file, 'r') 
		lines = f.readlines()
		f.close()

		for line in lines: 
			coord_str = line.strip().split(" ")
			if len(coord_str) == 2:
				#print coord
				coord = (int(coord_str[0]), int(coord_str[1])) 
				self.game_board.add_mission_block(coord)

		self.info_board.draw_remained_text(self.game_board.get_mission_block_num())
		self.info_board.draw_stage_text(self.stage)

		return True
		

	# 게임 스타트
	def start(self):
		self.generate_tetromino()
		self.after_id = self.tk.after(300, self.move_down_cur_tetromino)

		self.tk.mainloop()

	def move_down_cur_tetromino(self):
		if self.cur_tetromino is not None:
			self.move_cur_tetromino("down")
			self.after_id = self.tk.after(300, self.move_down_cur_tetromino)

	def move_cur_tetromino(self, direction):
		if self.cur_tetromino is None:
			return False

		if not self.cur_tetromino.move(direction):
			if direction == "down":
				# 바닥에 닿았을 경우(Landed)
				self.game_board.check_for_complete_row(self.cur_tetromino)
				remained = self.game_board.get_mission_block_num()
				self.info_board.draw_remained_text(remained)
				self.cur_tetromino = None
				

				if remained == 0:
					tkMessageBox.showwarning(title="Good!", message="스테이지%d Clear!" % self.stage)
					self.game_board.clear()
					self.stage += 1
					if not self.load_stage():
						tkMessageBox.showwarning(title="Good", message="축하합니다~끝", parent=self.tk)
						self.tk.destroy()
						sys.exit(0)

					self.tk.after_cancel(self.after_id )
					self.generate_tetromino()
					self.after_id = self.tk.after(300, self.move_down_cur_tetromino)
					return False


				self.generate_tetromino()

				if self.cur_tetromino is None:
					tkMessageBox.showwarning(title="Game Over!", message="Game Over!", parent=self.tk)
					self.tk.destroy()
					sys.exit(0)

				return False

		return True

	# 테크노미노 생성 
	def generate_tetromino(self):
		next_tetromino_class = self.tetrominoes[randint(0, len(self.tetrominoes)-1)]
		self.info_board.draw_next_tetromino(next_tetromino_class)

		if self.next_tetromino_class is not None:
			self.cur_tetromino = self.next_tetromino_class.create(self.game_board)
		else:
			self.cur_tetromino = Tetromino_J.create(self.game_board)

		self.next_tetromino_class = next_tetromino_class

	# 키다운 콜백함수 
	def callback_left(self, event):
		self.move_cur_tetromino("left")

	def callback_right(self, event):
		self.move_cur_tetromino("right")

	def callback_down(self, event):
		self.move_cur_tetromino("down")

	def callback_space(self, event):
		while self.move_cur_tetromino("down"):
			pass

	def callback_rotate(self, event):
		if self.cur_tetromino is not None:
			self.cur_tetromino.rotate()

	def callback_pass_stage(self, event):
		self.game_board.mission_block_set.clear()
		while self.move_cur_tetromino("down"):
			pass

# ------------------------------
# M A I N
# ------------------------------
if __name__ == "__main__":
	tetris = Tetris()
	tetris.start()


