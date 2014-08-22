import sys
import shelve
from ast import literal_eval

def preview_dict(in_dict, limit = 10):
    num_shown = 0
    for key in in_dict:
        value = in_dict[key]
        print("{:15}  -> {}".format(key, value))
        num_shown += 1
        if num_shown == limit:
            break

def f_measure_tf(tp,tn,fp,fn):
    try:
        precision = tp / float(tp+fp)
        recall = tp / float(tp + fn)
        f_measure = 2*precision*recall/(precision + recall)
        accuracy = float(tp + tn) / (tp + tn + fp + fn)
        balanced_accuracy = 0.5 * (float(tp)/(tp + fn) + float(tn)/(tn+fp))  
        print("%12s = %1.3f" % ('Precision', precision))
        print("%12s = %1.3f" % ('Recall', recall))
        print("%12s = %1.3f" % ('F-measure', f_measure))
        print("%12s = %1.3f" % ('Accuracy', accuracy))
        print("%12s = %1.3f" % ('Bal. Accuracy', balanced_accuracy))
    except:
        f_measure = 0
    return f_measure

###!  CHANGE THE BELOW!!!!!

def invert_list_dict(list_dict, remove_duplicates = True):
    """
    Switch the values list contents to keys and the keys to values in lists.
    
    Use remove_duplicates to remove new keys that are ambiguous.
    """
    
    inv_dict = {}
    
    for key in list_dict:
        for entry in list_dict[key]:
            dict_append(inv_dict, entry, key)
    
    for key in inv_dict:
        inv_dict[key] = list(set(inv_dict[key]))
    
    if remove_duplicates:
        inv_dict_no_dups = {}
        for key in inv_dict:
            entries = list(set(inv_dict[key]))
            if len(entries) == 1:
                inv_dict_no_dups[key] = entries[0]
        return inv_dict_no_dups
                
    else:
        return inv_dict
    

def dict_append(app_dict,key,value, ignore_duplicates = False):
    """
    If a key is present in the dictionary append value to its value, else create a new entry with value as first member of list.
    """
    if key in app_dict:
        if ignore_duplicates:
            if value not in app_dict[key]:
                app_dict[key].append(value) 
        else:
            app_dict[key].append(value)
    else:
        app_dict[key] = [value]

def dict_count(count_dict, key):
    """
    If key is in count_dict add 1 to key's value, else add key to count_dict with value 1.
    """
    if key in count_dict:
        count_dict[key] += 1
    else:
        count_dict[key] = 1
    
    
    
def class_join(join_list, join_string, attr = None):
    """
    For a list of classes, join the strings of those classes using the join string.
    
    If attr is a valid attribute of classes in join_list, join that attribute 
    """
    
    strings = []
    
    if (attr is not None) & hasattr(join_list[0], attr):
        for join_class in join_list:
            strings.append(str(getattr(join_class, attr)))
    else:
        for join_class in join_list:
            strings.append(str(join_class))
    
    return join_string.join(strings)

class loop_counter:
    """Use to track progress of a loop of known length."""
    
    def __init__(self, length, message = 'Entering loop'):
    
        self.length = length
        self.num_done = 0
        self.next_progress = 1
        
        print("{}".format(message))
        
        sys.stdout.write("\r - %d %%" % self.num_done)
        sys.stdout.flush()
    
    def step(self, number = None):
        self.num_done += 1
        if ((100 * self.num_done) / self.length) > self.next_progress:
            number = self.num_done
            if number is not None:
                sys.stdout.write("\r - %d %%  (%d / %d)" % (self.next_progress, number, self.length))
            else:
                sys.stdout.write("\r - %d %%" % self.next_progress)
            sys.stdout.flush()
            self.next_progress += 1
    
    def stop(self):
        sys.stdout.write("\r - 100 %\n")
        sys.stdout.flush()
        
# def load_shelf(shelf_file):
#     shelf = shelve.open(shelf_file)
#     
#     for key in shelf:
#         command = key + " = shelf['" + key + "']"
#         print command
#         exec(command)

def count_lines(filename):
    num_lines = 0
     
    f_in = open(filename, 'r')
    for line in f_in:
        num_lines += 1
    
    f_in.close()
    return num_lines
    
    
    
     
    
    
    