
def make_iter(list1,list2):
    for item1 in list1:
        if isinstance(item1, str):
            for item2 in list2:
                if isinstance(item2, str):
                    yield(item1 + item2)
                else:
                    for q in make_iter([item1],item2):
                        yield q
                    
        else:
            for q in make_iter(item1,list2):
                yield q

def main():
    qs = [['A','Q'],'B']
    rs = ['C',[['D','X'],'R']]
    
    new_iter = make_iter(qs,rs)
    print(new_iter)
    
    for item in new_iter:
        print item




if __name__ == '__main__':
    main()