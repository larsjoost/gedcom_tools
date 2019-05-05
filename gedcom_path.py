from fuzzywuzzy import process

class Family:
    def __init__(self, identifier, population):
        self.identifier = identifier
        self.population = population
        self.husbond = None
        self.wife = None
        self.children = []
    def to_string(self):
        return "Husbond: " + self.population.get_name(self.husbond) + \
            ", wife: " + self.population.get_name(self.wife) + \
            ", children: " + str(self.population.get_names(self.children))
    def __repr__(self):
        return self.to_string()
    def __str__(self):
        return self.to_string()
    
class Individual:
    def __init__(self, identifier):
        self.identifier = identifier
        self.name = None
        self.children = []
        self.families = []
        self.parent_family = None

class Population:
    def __init__(self):
        self.individuals = {}
    def add_individual(self, individual):
        self.individuals[individual.identifier] = individual
    def add_child(self, identifier, child):
        if identifier is not None:
            self.individuals[identifier].children.append(child)
    def add_children(self, identifier, children):
        for i in children:
            self.add_child(identifier, i)
    def get_individual(self, identifier):
        return self.individuals[identifier]
    def get_name(self, identifier):
        return self.individuals[identifier].name
    def get_names(self, identifiers=None):
        if identifiers is None:
            identifiers = self.individuals.keys()
        return [self.get_name(i) for i in identifiers]
    def get_identifier(self, name):
        for i in self.individuals.keys():
            if name == self.individuals[i].name:
                return self.individuals[i].identifier
        return None
    def get_identifiers(self):
        return self.individuals.keys()

class AST:
    def __init__(self):
        self.elements = []
    def get_element(self, level):
        while level >= 0:
            element = self.element.last()
            level -= 1
        return element
            
    def add(self, level, first_word, second_word, rest):
        pass
        
fname = '55dkh1_3530818cc9j55ydc45ader.ged'

with open(fname) as f:
    content = f.readlines()

population = Population()

current_individual = None

families = {}
current_family = None

line_number = 0

for line in content:
    line_number += 1
    words = line.split()
    try:
        if words[0] == "0":
            current_individual = None
            current_family = None
            identifier = words[1]
            if words[2] == "INDI":
                current_individual = Individual(identifier)
                population.add_individual(current_individual)
            elif words[2] == "FAM":
                current_family = Family(identifier, population)
                families[identifier] = current_family
    except IndexError:
        pass
    if current_individual is not None and len(words) > 1:
        if words[1] == "NAME":
            name = line.split(' ', 2)[2].strip()
            name = name.replace('/','')
            current_individual.name = name
        elif words[1] == "FAMS":
            current_individual.families.append(words[2])
        elif words[1] == "FAMC":
            assert current_individual.parent_family is None
            current_individual.parent_family = words[2]
    elif current_family is not None and len(words) > 1:
        if words[1] == "CHIL":
            #if len(current_family.children) > 10:
            #    raise Exception, "Line " + str(line_number) + ": Family " + str(families)
            current_family.children.append(words[2])
        elif words[1] == "HUSB":
            current_family.husbond = words[2]
        elif words[1] == "WIFE":
            current_family.wife = words[2]


for i in families.keys():
    family = families[i]
    population.add_children(family.husbond, family.children)
    population.add_children(family.wife, family.children)
            
# i = "@I500324@"

# individual = population.get_individual(i)

# print individual.children

# exit(1)
    
#ancester_name = "Carl Frederik Andreas Julius"

#ancester_name = "Casper Thede Keifler"        

#ancester_name = "Anna Elisabeth Storm"        

#ancester_name = "Marie Kirstine Poulsen Vedal"

#ancester_name = "Peder Knudsen Storm"
#ancester_name = "Peder Nissen Vedel"
#ancester_name = "Hans Laugesen"
#ancester_name = "Ebbe Skjalmsen Hvide"
# ancester_name = "Valdemar Bernhard Joost"

#ancester_name = "Ragnar Lodbrok"

ancester_name = "Hans Tausen"

descendent_name = "Anne Joost Jensen"

found_ancester = process.extractOne(ancester_name, population.get_names())[0]

ancester_id = population.get_identifier(found_ancester)

print "Searched for ancester", ancester_name, ". Found", found_ancester, "with id", ancester_id 

def get_children(identifier):
    return population.get_individual(identifier).children

def get_name_and_id(identifier):
    return get_name(identifier) + "(" + identifier + ")"

ancester_children = get_children(ancester_id)

if ancester_children is not None:
    print "Ancester children =", ancester_children
    
found_descendent = process.extractOne(descendent_name, population.get_names())[0]

descendent_id = population.get_identifier(found_descendent)

print "Searched for descendent", descendent_name, ". Found", found_descendent, "with id", descendent_id

def print_info(identifier, print_family=False):
    print population.get_individual(identifier).name
    
def search_tree(id):
    found_descendent = False
    if descendent_id == id:
        print "# Family branch start"
        print_info(id)
        found_descendent = True
    else:
        children = get_children(id)
        if children is not None:
            for child in children:
                if search_tree(child):
                    print_info(id)
                    found_descendent = True
    return found_descendent
    

if search_tree(ancester_id):
    print_info(ancester_id)
else:
    print "Could not find descendent", descendent_name, "of ancester", ancester_name 

print_info(ancester_id, True)
