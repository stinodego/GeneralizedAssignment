from frozendict import frozendict

class GeneralizedAssignment():
    """
    Find the assignment that offers the maximum profit.
    
    Special version of the Generalized Assignment Problem, that allows agents
    to be assigned to more than one task.
    
    Assignments are generated through depth-first search, expanding most 
    promising nodes first. True maximum assignment is guaranteed when
    algorithm is allowed to complete. Otherwise, the assignment printed last
    may be used as a best guess.
    
    Optional 'complete' parameter requires agents and tasks to fully use
    their budgets.
    
    Optional 'fair' parameter maximizes the profits related to the least
    profitable task (and thus equalizes the profits among tasks).
    """
    
    def __init__(self, agents, tasks, 
                 agent_budget=lambda a: 1,
                 agent_cost=lambda a, t: 1,
                 task_budget=lambda a: 1,
                 task_cost=lambda a, t: 1,
                 profit=lambda a, t: 1,
                 hard_assignment=False,
                 complete=False,
                 fair=False,
                 verbose=True):
        
        # Register class variables
        self.agents = agents
        self.tasks = tasks
        self.agent_budget = agent_budget
        self.agent_cost = agent_cost
        self.task_budget = task_budget
        self.task_cost = task_cost
        self.profit = profit
        
        self.hard_assignment = hard_assignment
        self.complete = complete
        self.fair = fair
        self.verbose = verbose
        
        # Initialize dictionary of finished assignments and profits
        self.finished_assignments = {}
        self.max_profit = 0
        self.fair_profit = 0
        
        # Find all possible assignments
        init_assignment = self.initialize_assignment()
        
        self.assign({init_assignment})
        
        # Print the best assignment
        if self.verbose: self.print_stats()
    
    
    ######################
    ### MAIN FUNCTIONS ###
    ######################
    
    def initialize_assignment(self):
        """Initialize the assignment state."""
        # Initialize empty frozensets for each agent
        init_assignment = frozendict({a:frozenset() for a in self.agents})
        
        # Add hard assignments
        if self.hard_assignment:
            init_dict = dict(init_assignment)
            for a, t in self.hard_assignment.items():
                init_dict[a] = init_dict[a] | t
            init_assignment = frozendict(init_dict)
            
        return init_assignment
    
    def assign(self, starts):
        """Perform depth-first search.
        
        Expanding most promising nodes first. True maximum assignment is
        guaranteed when algorithm is allowed to complete. Otherwise, the 
        assignment printed last may be used as a best guess.
        """
        # Initialize the set of open and closed nodes, and the connection map
        open_set, closed_set = starts, set()
        
        # Initialize a map of assignments and associated profits
        profits = {s:0 for s in starts}
        
        while open_set:

            # Explore the most promising node
            current = max(open_set, key=lambda n: profits[n])
            
            # Move the current node from the open set to the closed set
            open_set.remove(current)
            closed_set.add(current)
            
            # Track if assignment is complete
            assignment_finished = True
            
            # Determine all possible next assignment steps
            for agent in self.agents:
                # Determine possible tasks the agent may be assigned to
                poss_tasks = self.assign_agent(agent, current)
                
                # If assignments are possible, the assignment is not complete
                if poss_tasks: assignment_finished = False
                
                for task in poss_tasks:
                    # Determine next assignment step
                    next_dict = dict(current)
                    next_dict[agent] = next_dict[agent] | {task}
                    next_assignment = frozendict(next_dict)
                    
                    # If we have already explored this assignment, continue
                    if next_assignment in closed_set:
                        continue
                    # Else add the assignment to the open set
                    else:
                        open_set.add(next_assignment)
                        profits[next_assignment] = self.calc_profit(next_assignment)
                    
            # If assignment is finished, add it to finished assignments
            if assignment_finished:
                
                # Check if assignment is also complete
                if self.complete and not self.is_complete(current):
                    continue
                
                self.finished_assignments[current] = profits[current]
                
                # Update current fair / max profit and print if applicable
                # Procedure for fair profit (max profit tiebreaker)
                if self.fair:
                    cur_fair_profit = self.calc_fair_profit(current)
                    if ((cur_fair_profit > self.fair_profit) or 
                        (cur_fair_profit == self.fair_profit and
                         profits[current] > self.max_profit)):
                        self.fair_profit = cur_fair_profit
                        self.max_profit = profits[current]
                        self.print_assignment(current, profits[current])
                    elif (self.verbose and profits[current] >= self.max_profit
                          and cur_fair_profit >= self.fair_profit):
                        self.print_assignment(current, profits[current])
                # Procedure for maximum profit
                else:
                    if profits[current] > self.max_profit:
                        self.max_profit = profits[current]
                        self.print_assignment(current, profits[current])
                    elif self.verbose and profits[current] >= self.max_profit:
                        self.print_assignment(current, profits[current])

    def assign_agent(self, agent, assignment):
        """
        Determine possible assignments for a single agent.
        
        Input: agent, assignment definition, current assignment
        Output: list of possible tasks the agent may be assigned to
        """
        
        # Calculate remaining budget for agent
        remaining_budget = self.calc_agent_budget(agent, assignment)
        
        # Determine which tasks the agent has budget for
        tasks_in_budget = {t for t in self.tasks
                           if self.agent_cost(agent, t) <= remaining_budget}
        
        # Agent cannot be assigned to the same task twice
        tasks_in_budget = {t for t in tasks_in_budget if t not in assignment[agent]}
        
        # Determine which tasks have enough budget remaining for the agent
        possible_tasks = []
        for task in tasks_in_budget:
            remaining_task_budget = self.calc_task_budget(task, assignment)
            if self.task_cost(agent, task) <= remaining_task_budget:
                possible_tasks.append(task)
                
        return sorted(possible_tasks)

    ########################
    ### HELPER FUNCTIONS ###
    ########################

    def calc_agent_budget(self, agent, assignment):
        """Calculate remaining budget for agent given the current assignment."""
        budget_spent = sum([self.agent_cost(agent, t) for t in assignment[agent]])
        return self.agent_budget(agent) - budget_spent

    def calc_task_budget(self, task, assignment):
        """Calculate remaining budget for a task given the current assignment."""
        # Get the agents assigned to this task
        agents_assigned = {a for a, tasks in assignment.items() if task in tasks}
        budget_spent = sum([self.task_cost(a, task) for a in agents_assigned])
        return self.task_budget(task) - budget_spent

    def calc_profit(self, assignment):
        """Calculate the profit for a given assignment."""
        return sum([self.profit(agent, task)
                    for agent, tasks in assignment.items() 
                    for task in tasks])

    def calc_fair_profit(self, assignment):
        """Calculate the fair profit for a given assignment."""
        fair_profit = {t:0 for t in self.tasks}
        for agent, tasks in assignment.items():
            for task in tasks:
                fair_profit[task] += self.profit(agent, task)
        return min(fair_profit.values())

    def is_complete(self, assignment):
        """A check whether a finished assignment is also complete."""
        for a in self.agents:
            if self.calc_agent_budget(a, assignment):
                return False
        for t in self.tasks:
            if self.calc_task_budget(t, assignment):
                return False
        return True

    #######################
    ### PRINT FUNCTIONS ###
    #######################

    def print_assignment(self, a, profit):
        """Prettily print an assignment on a single line."""
        a_list = sorted((a,sorted(t)) for a, t in a.items()) 
        a_string = ', '.join(['({}: {})'.format(a, ', '.join(t)) for a, t in a_list])
        print('{} - {}'.format(profit, a_string))
    
    def print_stats(self):
        """Print assignment stats and one max profit assignment."""
        # Determine assignments with the maximum profit
        max_assignments = [a for a,p in self.finished_assignments.items()
                           if p == self.max_profit]
        
        # Print general stats
        print('\nTotal number of assignments: {}'.format(len(self.finished_assignments)))
        if self.fair:
            print('Maximum fair profit: {}'.format(self.max_profit))
            print('Number of max fair profit assignments: {}\n'.format(len(max_assignments)))
        else:
            print('Maximum profit: {}'.format(self.max_profit))
            print('Number of max profit assignments: {}\n'.format(len(max_assignments)))
        
        # Pretty print a single max assignment
        if max_assignments:
            print('Example of a maximum profit assignment:')
            for a, t in sorted((a,sorted(t)) for a, t in max_assignments[0].items()):
                print('Agent: {}\tTasks: {}'.format(a, ', '.join(t)))


########################################
### ASSIGNMENT PROBLEM SPECIFICATION ###
########################################

def main():

    # Easy assignment problem
    agents = {'a', 'b', 'c'}
    tasks = {'t1', 't2'}

    agent_budget = {'a': 1, 'b': 2, 'c': 1}
    agent_cost = lambda a, t: 1
      
    task_budget = {'t1': 2, 't2': 2}
    task_cost = lambda a, t: 1
       
    profit = {('a', 't1'): 3, ('b', 't1'): 1, ('c', 't1'): 2,
              ('a', 't2'): 1, ('b', 't2'): 3, ('c', 't2'): 2}
        
    # Optional hard assignments (map of agent: set of tasks)
    hard_assignment = {}#{'thorsten': {'rogier'}}

    # Calculate maximum assignment
    GeneralizedAssignment(agents, tasks, lambda a: agent_budget[a], agent_cost,
                          lambda t: task_budget[t], task_cost,
                          lambda a, t: profit[(a,t)],
                          hard_assignment=hard_assignment,
                          complete=True,
                          fair=True)

if __name__ == "__main__":
    main()