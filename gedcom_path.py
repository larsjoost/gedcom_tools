#!/usr/bin/python3

import sys, getopt, operator, datetime

from fuzzywuzzy import process
from fuzzywuzzy import fuzz

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
    def parse_command(self, line_parser):
        if line_parser.command[0] == "CHIL":
            self.children.append(line_parser.command[1])
        elif line_parser.command[0] == "HUSB":
            self.husbond = line_parser.command[1]
        elif line_parser.command[0] == "WIFE":
            self.wife = line_parser.command[1]

class Date:
    def __init__(self, date):
        self.date = date
    def is_datetime(self):
        return isinstance(self.date, datetime.datetime)
    def get_year(self):
        if self.is_datetime():
            return self.date.date().year
        return None
    def __str__(self):
        if self.is_datetime():
            return str(self.get_year())
        else:
            return self.date
    def year_difference(self, date):
        if date is not None:
            y1 = self.get_year()
            y2 = date.get_year()
            if y1 is not None and y2 is not None:
                return abs(y1 - y2)
        return None
    def is_year_difference_below(self, data, limit):
        d = self.year_difference(data)
        if d is not None:
            return (d < limit)
        return None
    
class DateParser:
    def _parse(self, date):
        supported_formats = ["%d %b %Y", "%Y", "ABT %Y", "AFT %Y", "BEF %Y"]
        for i in supported_formats:
            try:
                parsed_date = datetime.datetime.strptime(date, i)
                return parsed_date
            except ValueError:
                pass
        return date
    def parse(self, date):
        return Date(self._parse(date))
    
class IndividualBirthParser:
    def __init__(self, line_parser):
        self.date = None
        self.index = line_parser.index
        self.date_parser = DateParser()
    def parse_command(self, line_parser):
        if line_parser.index <= self.index:
            return None
        if line_parser.command[0] == "DATE":
            self.date = self.date_parser.parse(line_parser.rest)
        return self
    
class Individual:
    def __init__(self, identifier):
        self.identifier = identifier
        self.name = None
        self.children = []
        self.families = []
        self.parent_family = None
        self.gender = None
        self.birthday = None
        self._birth_parser = None
    def __repr__(self):
        return self.name + ", children = " + str(self.children)
    def parse_command(self, line_parser):
        if self._birth_parser is not None:
            if self._birth_parser.parse_command(line_parser) is None:
                self.birthday = self._birth_parser.date
                self._birth_parser = None
        if self._birth_parser is None:
            if line_parser.command[0] == "BIRT":
                self._birth_parser = IndividualBirthParser(line_parser)
            elif line_parser.command[0] == "NAME":
                name = line_parser.rest
                name = name.replace('/','')
                self.name = name
            elif line_parser.command[0] == "FAMS":
                self.families.append(line_parser.command[1])
            elif line_parser.command[0] == "FAMC":
                assert self.parent_family is None
                self.parent_family = line_parser.command[1]
            elif line_parser.command[0] == "SEX":
                self.gender = line_parser.command[1]
            
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
    def get_gender(self, identifier):
        return self.individuals[identifier].gender
    def does_gender_match(self, a, b):
        return self.get_gender(a) == self.get_gender(b)
    def is_year_difference_below(self, a, b, limit):
        y1 = self.get_birthday(a)
        y2 = self.get_birthday(b)
        y = None
        if y1 is not None and y2 is not None:
            y = y1.is_year_difference_below(y2, limit)
        if y == None:
            y = True
        return y
    def get_birthday(self, identifier):
        return self.individuals[identifier].birthday
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

    def search_ancester_tree(self, id, descendent_id):
        tree = None
        if descendent_id == id:
            tree = [[]]
        else:
            children = self.get_children(id)
            if children is not None:
                for child in children:
                    child_tree = self.search_ancester_tree(child, descendent_id)
                    if child_tree is not None:
                        for i in child_tree:
                            i.append(child)
                        if tree is None:
                            tree = child_tree
                        else:
                            tree.extend(child_tree)
        return tree

    def search_tree(self, ancester_id, descendent_id):
        tree = self.search_ancester_tree(ancester_id, descendent_id)
        if tree is not None:
            for i in tree:
                i.append(ancester_id)
        return tree

    def get_branches(self, ancester_name, descendent_name, contains_names):
        ancester_id = self.get_identifier(ancester_name)
        descendent_id = self.get_identifier(descendent_name)
        tree = self.search_tree(ancester_id, descendent_id)
        matched_branches = []
        if tree is not None:
            for branch in tree:
                matches = True
                for x in contains_names:
                    if self.get_identifier(x) not in branch:
                        matches = False
                if matches:
                    matched_branches.append(branch)
        return matched_branches

    def apply_format(self, identifier, format):
        x = format
        x = x.replace("%n", self.get_name(identifier))
        x = x.replace("%g", self.get_gender(identifier))
        x = x.replace("%b", str(self.get_birthday(identifier)))
        return x
    def print_branches(self, tree, format):
        count = 1
        for branch in tree:
            print("# Branch number " + str(count))
            for x in branch:
                print(self.apply_format(x, format))
            count += 1

class IndividualDoubles:

    def print_doubles(self, doubles):
        for i in doubles:
            print(str(i))
            
    def get_doubles(self, population, identifiers, size):
        doubles = []
        dot_size = 10000
        match_display_size = 100 * dot_size
        count = 0
        print("Searching through " + str(len(identifiers)) + " names to find doubles." +
              " A dot printed on screen means that " + str(dot_size) +
              " name matches has been calculated...")
        for i in identifiers:
            for j in identifiers:
                if i != j and population.does_gender_match(i, j) and population.is_year_difference_below(i, j, 5):
                    name_i = population.get_name(i)
                    name_j = population.get_name(j)
                    if len(name_i) > 0 and len(name_j) > 0:
                        first_letter_i = name_i[0].upper()
                        first_letter_j = name_j[0].upper()
                        if first_letter_i == first_letter_j:
                            score = fuzz.ratio(name_i, name_j)
                            if score < 100:
                                if len(doubles) > 0:
                                    lowest_score, name1, id1, name2, id2 = doubles[-1]
                                else:
                                    lowest_score = 0
                                if score > lowest_score:
                                    match_exists = False
                                    for s, n1, i1, n2, i2 in doubles:
                                        if (i in (i1, i2)) and (j in (i1, i2)):
                                            match_exists = True
                                            break
                                    if not match_exists:
                                        doubles.append((score, name_i, i, name_j, j))
                                        doubles.sort(key=operator.itemgetter(0), reverse=True)
                                        doubles = doubles[0:size]
                if (count % dot_size) == 0:
                    sys.stdout.write('.')
                    sys.stdout.flush()
                if (count % match_display_size) == 0:
                    print()
                    self.print_doubles(doubles)
                count += 1
        return doubles
    
class LineParser:
    def __init__(self):
        self.line_number = 0
        self.clear_values()
    def clear_values(self):
        self.command = [None, None]
        self.rest = None
        self.index = None
    def is_int(self, text):
        try:
            int(text)
            return True
        except ValueError:
            return False
    def parse_next_line(self, content, valid_command):
        self.line_number += 1
        return self.parse_line(content, valid_command)
    def parse_line(self, content, valid_command):
        try:
            line = content[self.line_number]
        except IndexError:
            return valid_command
        words = line.split()
        try:
            index = words[0]
        except IndexError:
            return self.parse_next_line(content, valid_command)
        if not valid_command:
            if self.is_int(index):
                self.index = int(index)
                valid_command = True
                self.command[0:2] = words[1:3]
                try:
                    self.rest = line.split(' ', 2)[2].strip()
                except IndexError:
                    self.rest = None
                return self.parse_next_line(content, valid_command)
            else:
                print("Line " + str(self.line_number) + " does not begin with integer: '" + index + "' " + str([ord(i) for i in index]))
                print(line)
        elif not self.is_int(index): 
            self.rest += line
            self.parse_next_line(content, valid_command)
        return valid_command
    
    def next_command(self, content):
        return self.parse_line(content, False)
        
class FileParser:
                    
    def parse_file(self, content, population):
        line_parser = LineParser()
        current_parser = None
        families = {}
        while line_parser.next_command(content):
            if line_parser.index == 0:
                current_parser = None
                try:
                    identifier = line_parser.command[0]
                    if line_parser.command[1] == "INDI":
                        current_parser = Individual(identifier)
                        population.add_individual(current_parser)
                    elif line_parser.command[1] == "FAM":
                        current_parser = Family(identifier, population)
                        families[identifier] = current_parser
                except IndexError:
                    pass
            elif current_parser is not None:
                current_parser.parse_command(line_parser)

        for i in families.keys():
            family = families[i]
            population.add_children(family.husbond, family.children)
            population.add_children(family.wife, family.children)

def usage():
    print('gedcom_path.py -f <filename> -n <list> -d <number> -x <format>')
    
def main(argv):
    inputfile = None
    names = None
    number_of_doubles = None
    format = "%n"
    try:
        opts, args = getopt.getopt(argv,"hf:n:d:x:",["ifile=","ofile="])
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
        elif opt == "-d":
            number_of_doubles = int(arg)
        elif opt == "-x":
            format = arg

    if inputfile is None:
        print("Input file missing")
        usage()
        sys.exit(2)

    with open(inputfile, 'r', errors='replace', encoding='utf-8-sig') as f:
        content = f.readlines()

    population = Population()
    file_parser = FileParser()
    file_parser.parse_file(content, population)

    if names is not None:

        names = [population.find_closest_match(i) for i in names]

        if len(names) > 1:
            descendent_name = names[0]
            ancester_name = names[-1]
            contains_names = names[1:-1]
            tree = population.get_branches(ancester_name, descendent_name, contains_names)
            population.print_branches(tree, format)
            if number_of_doubles is not None:
                individual_doubles = IndividualDoubles()
                identifiers = [i for sublist in tree for i in sublist]
                doubles = individual_doubles.get_doubles(population, identifiers, number_of_doubles)
                individual_doubles.print_doubles(doubles)
        else:
            name = names[0]
            id = population.get_identifier(name)
            children = population.get_children(id)
            print("Name = " + name)
            print("Children:")
            for i in children:
                print(population.get_name(i))

    elif number_of_doubles is not None:
        i = IndividualDoubles()
        identifiers = population.get_identifiers()
        doubles = i.get_doubles(population, identifiers, number_of_doubles)
        i.print_doubles(doubles)
        
if __name__ == "__main__":
   main(sys.argv[1:])

