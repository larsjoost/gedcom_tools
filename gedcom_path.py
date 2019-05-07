#!/usr/bin/python

import sys, getopt

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
    def __repr__(self):
        return self.name + ", children = " + str(self.children)
        
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
    def find_closest_match(self, name):
        return process.extractOne(name, self.get_names())[0]
    def get_children(self, identifier):
        return self.get_individual(identifier).children
    def get_name_and_id(self, identifier):
        return self.get_name(identifier) + "(" + identifier + ")"
    def print_info(self, identifier, print_family=False):
        print(self.get_individual(identifier).name)

    def search_tree(self, id, descendent_id):
        tree = None
        if descendent_id == id:
            tree = [[]]
        else:
            children = self.get_children(id)
            if children is not None:
                for child in children:
                    child_tree = self.search_tree(child, descendent_id)
                    if child_tree is not None:
                        for i in child_tree:
                            i.append(self.get_name(child))
                        if tree is None:
                            tree = child_tree
                        else:
                            tree.extend(child_tree)
        return tree

    def print_path(self, ancester_name, descendent_name, contains_names):
        found_ancester = self.find_closest_match(ancester_name)
        ancester_id = self.get_identifier(found_ancester)
        print("Searched for ancester " + ancester_name + ". Found " + found_ancester + " with id " + ancester_id) 
        ancester_children = self.get_children(ancester_id)
        if ancester_children is not None:
            print("Ancester children = " + str(ancester_children))
        found_descendent = self.find_closest_match(descendent_name)
        descendent_id = self.get_identifier(found_descendent)
        print("Searched for descendent " + descendent_name + ". Found " + found_descendent + " with id " + descendent_id)
        tree = self.search_tree(ancester_id, descendent_id)
        if tree is not None:
            count = 0
            similar_count = 0
            for i in tree:
                i.append(self.get_name(ancester_id))
                matches = 0
                for x in tree:
                    if x == i:
                        matches += 1
                for x in contains_names:
                    if x not in i:
                        matches = 0
                if matches == 1:
                    count += 1
                    print("# Branch number " + str(count))
                    print(i)
                elif matches > 1:
                    similar_count += 1
        else:
            print("Could not find descendent " + descendent_name + " of ancester " + ancester_name) 

class FileParser:
    def parse_file(self, content, population):
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
                    current_family.children.append(words[2])
                elif words[1] == "HUSB":
                    current_family.husbond = words[2]
                elif words[1] == "WIFE":
                    current_family.wife = words[2]

        for i in families.keys():
            family = families[i]
            population.add_children(family.husbond, family.children)
            population.add_children(family.wife, family.children)
            


def usage():
    print('gedcom_path.py -f <filename> -n <list>')
    
def main(argv):
    inputfile = None
    names = None
    try:
        opts, args = getopt.getopt(argv,"hf:n:",["ifile=","ofile="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)
    for opt, arg in opts:
        if opt == '-h':
            usage()
            sys.exit()
        elif opt in ("-f", "--ifile"):
            inputfile = arg
        elif opt == "-n":
            names = arg.split(',')

    if inputfile is None:
        print("Input file missing")
        usage()
        sys.exit(2)

    if names is None:
        print("Name list is missing")
        usage()
        sys.exit(2)
        
    with open(inputfile, 'r', errors='replace') as f:
        content = f.readlines()

    population = Population()
    file_parser = FileParser()
    file_parser.parse_file(content, population)

    names = [population.find_closest_match(i) for i in names]
     
    if len(names) > 1:
        descendent_name = names[0]
        ancester_name = names[-1]
        contains_names = names[1:-1]
        population.print_path(ancester_name, descendent_name, contains_names)
    else:
        name = names[0]
        id = population.get_identifier(name)
        children = population.get_children(id)
        print("Name = " + name)
        print("Children:")
        for i in children:
            print(population.get_name(i))
        
if __name__ == "__main__":
   main(sys.argv[1:])

