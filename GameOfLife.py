import sys, time, re, builtins, traceback, copy, argparse

#Manage the game
class GameManager:
    is_windows = None
    grid = None
    with_color = None
    rules = {}
    
    def __init__(self, with_color, rules_file, configs,symbols):
        self.is_windows = sys.platform.startswith('win')
        if self.is_windows:
            # Check if windows
            print("Windows is broken...")
            print("Please run on Linux next time!")
        self.rules = self.get_rules(rules_file)
        self.grid = Grid(configs,self.rules,symbols)
        self.with_color = with_color
    
    # Make game run itself or step-by-step
    def play(self, update_time,step, frames, shitty):
        times = 0
        try:
            while True:
                # check if there is a defined number of frames and if we have reached it
                if times is frames:
                    sys.exit()             
                output = []
                times += 1
                # Build array with symbol ready to print
                for line in self.grid.grid_arr:
                    for cell in line:
                        if cell.is_alive and self.with_color:
                            output.append(cell.content.symbol + " ")
                        elif cell.is_alive :
                            output.append(cell.content.race + " ")
                        else:
                            output.append(". ")
                    output.append("\n")
                # check if windows since windows doesn't support 
                # escape sequence correctly
                if self.is_windows or shitty:
                    print("".join(output))
                else:
                    self.out("".join(output))
                # if step mode, wait for input (such as enter)
                if step:
                    input()
                    # move to cursor at the beginning of stdout
                    # making it updating screen instead of print 100 newlines
                    sys.stdout.write(('\b\r'))
                    sys.stdout.flush()
                else:
                    time.sleep(update_time)
                self.grid.comp_next_grid()
        except KeyboardInterrupt:
                print("\nGoodbye!")
    
    # Fetch rules from rules file
    def get_rules(self, rules_file):
        all_rules = {}
        try:
            with open(rules_file) as rf:
                for line in rf:
                    # parse one rule (ex: "R:4,4,5") 
                    # only 1 char/param since no more than 8 neighbours possible
                    some_rule = re.findall(r"[\w\d]",line)
                    all_rules[some_rule[0]] = some_rule[1:len(some_rule)]
        except IOError:
            print("Can't open rules file : "+ rules_file +"\n\n")
            sys.exit()
        return all_rules
    
    # Use to overwrite stdout and animate board instead of
    # overloading it with '\n' (much prettier)
    def out(self, txt):
        sys.stdout.write(str(txt))
        # for each '\n' in text, return to beginning of line and '\b'
        # so cursor goes to end of previous line
        for i in range(str(txt).count('\n')):
            sys.stdout.write(('\r\b'))
        #end that with carriage return so cursor's at the beginning
        sys.stdout.write(('\r'))
        sys.stdout.flush()
    

# class that contains the game grid 
class Grid:
    grid_arr = None
    symbols = None
    rules = None
    def __init__ (self, configs, rules,symbols):
        size_x = None
        size_y = None
        self.rules = rules
        # parse intial configs
        try:
            with open(configs) as cf:
                # read first line which is grid size
                size_x, size_y = cf.readline().split(",")
                size_x = int(size_x)
                size_y = int(size_y)
                # set the dictionary of symbols {$race:$symbol}
                self.symbols = symbols
                # initiate empty grid as 2 dimensions array of Cell
                self.grid_arr = [[Cell(i,j,self) for i in range (size_x)] for j in range(size_y)]
                # read all other lines which are intial cells
                for line in cf:
                    # fetch some cell data from file
                    race, pos_x, pos_y = line.split(",")
                    # set cell to born and if symbol doesnt exist for that race
                    # set it to None and Being.__init__ will make it to be the race character
                    try:
                        self.grid_arr[int(pos_y)][int(pos_x)].born(Being(race, self.symbols[race]))
                    except:
                        self.grid_arr[int(pos_y)][int(pos_x)].born(Being(race, None))
        except IOError:
            print("Can't open config file : "+ configs +"\n\n")
            sys.exit()
        except Exception:            
            print(traceback.format_exc())
            sys.exit()
        
    # Compute next grid
    def comp_next_grid(self):
        # deep copy since some cell will die/born in processus
        # but everything is checked with previous state
        grid_bu = copy.deepcopy(self.grid_arr)
        for line in self.grid_arr:
            for cell in line:
                # make cell check its next state
                cell.next_state(grid_bu)
                
            
# Represent each position in the game grid and contains or not a being        
class Cell:
    pos_x = None
    pos_y = None
    is_alive = False
    content = None
    grid = None
    
    def __init__ (self, pos_x, pos_y, grid):
        self.pos_x = pos_x
        self.pos_y = pos_y
        self.grid = grid
            
    def die(self):
        self.is_alive = False
        self.content = None
        
    def born(self, being):
        self.is_alive = True
        self.content = being
    
    #compute its next state relatively to the previous state (grid_bu)
    def next_state(self, grid_bu):
        alive_neigh = 0
        # count how many alive neighbour this cell have, position relative to itself
        # with y in [-1,0,1], x is in fact the delta y
        for y in range(-1,2):
            # with x in [-1,0,1], y is in fact the delta x
            for x in range(-1,2):
                neigh_x = self.pos_x + x
                neigh_y = self.pos_y + y
                # if neighbour is in the grid
                if neigh_x >= 0 and neigh_y >= 0 and neigh_y < len(grid_bu) and neigh_x < len(grid_bu[neigh_y]):
                    # if neighbour is alive
                    if grid_bu[neigh_y][neigh_x].is_alive:
                        # if not itself
                        if not(x is 0 and y is 0):
                            alive_neigh += 1
        if self.is_alive:
            try:
                # check rules for the type of cell we have here
                rules = self.grid.rules[self.content.race]
                # check if its over- or under-populated this cell dies
                # and contains no more being
                if alive_neigh < int(rules[1]) or alive_neigh > int(rules[2]):
                    self.die()                
            except KeyError:
                print("Race not specified in rules file : " + self.content.race)
                sys.exit()
        # if cell is dead
        else:
            # check sequentially in rules dictionary enabling priority
            #(first is the first added, so it's the first line to be read in rules file) 
            for key, value in self.grid.rules.items() :
                # if the number of alive neighbour is exactly the number required
                # for a cell of that type to born, make it happen then stop checking
                if alive_neigh is int(value[0]):
                    #Set cell to born and if symbol doesnt exist for that race
                    # set it to None and Being.__init__ will make it to be the race character                    
                    try:
                        self.born(Being(key,self.grid.symbols[key]))
                    except:
                        self.born(Being(key,None))
                    break
# basically contains the "genetic" information for cell
class Being:
    race = None
    symbol = None
    
    def __init__(self,race,symbol=None):
        # if no symbols are specified symbol become the race character
        if symbol is None:
            self.symbol = race
        else:
            self.symbol = symbol
        self.race = race


       
if __name__ == '__main__':
    
    color_mode = False
    rules = "rules.txt"
    configs = "config.txt"
    speed = 0.1
    step = False
    # Define symbols for each race
    symbols = {"R":"\033[91m#\033[0m", "B":"\033[94m#\033[0m","G":"\033[92m#\033[0m"}
    list_mode = True
    frames = None
    
    # Declare possible command line args
    parser = argparse.ArgumentParser()  
    parser.add_argument("-c", "--color", help="Set color mode ON", action="store_true")
    parser.add_argument("-e", "--step", help="Set step-by-step mode ON (press enter for next frame)", action="store_true")
    parser.add_argument("-m", "--matrix", help="Set matrix mode ON", action="store_true")
    parser.add_argument("-a", "--animation", help="Set animation mode ON", action="store_true")
    parser.add_argument("-s", "--speed", help="Set animation refresh speed for fluid mode", type=float)
    parser.add_argument("--config", help="Select initial configuration file")
    parser.add_argument("--rules", help="Select rules file")
    parser.add_argument('frames', type=int, nargs="?", help='number of frames (if there is none, it will run indefinitely)')  
    args = parser.parse_args()
    # check for number of frame to output if none infinite loop
    if args.frames is None:
        frames = None
    else:
        frames = int(args.frames)
    if args.animation:
        list_mode = False
    # Set frame update speed    
    if args.speed is not None and args.speed >= 0:
        speed = args.speed
    # Set the specified file to be the rules file
    if args.rules is not None:
        rules = args.rules
    # Set the specified file to be the configs file
    if args.config is not None:
        configs = args.config
    # if matrix mode set all visual to green
    if args.matrix:
        symbols = {"R":"\033[92m#\033[0m", "B":"\033[92m#\033[0m","G":"\033[92m#\033[0m"}
    step = args.step
    color_mode = args.color
    
    # init game
    gm = GameManager(color_mode,rules,configs,symbols)
    # start game
    gm.play(speed,step,frames,list_mode)