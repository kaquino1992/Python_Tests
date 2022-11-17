from __future__ import annotations
import typing
import bisect
import pickle #create bytestring object which you cans save and open at a later time
from typing import Any, List, Optional, Tuple, Union, Dict, Generic, TypeVar, cast, NewType
import math
#NUM_BLOCKS = 20
#BLOCK_SIZE = 4096
LOGGING = False

Address = NewType("Address", int)  # Address type

class Disk:
    __frozen = False

    def __init__(self):
        self.memory: List[bytearray] = [] #bytearray is an empty array that can store bytes
        self.__frozen = True

    def __setattr__(self, name: str, value) -> None:
        if self.__frozen:
            raise Exception("Internal error.")
        super.__setattr__(self, name, value)

    def verify(self):
        assert self == DISK, "Error. Did you override DISK?"

    def new(self) -> Address:
        self.verify()
        empty = bytearray(pickle.dumps(object())) #dumps saves a type string and then if you use loads it will "unpickle it" which means opening it
        self.memory.append(empty)
        if LOGGING:
            print(f"allocated block {len(self.memory) - 1}")
        return len(self.memory) - 1

    def read(self, addr: Address) -> "BTreeNode":
        self.verify()
        if (addr >= len(self.memory)):
            raise ValueError(f"Error: Memory address {addr} has not yet been allocated. You cannot read from it.")
        block = self.memory[addr]
        if LOGGING:
            print(f"read {pickle.loads(block)} at block {addr}")
        return pickle.loads(block)

    def write(self, addr: Address, data: "BTreeNode"):
        self.verify()
        if str(type(data)) != "<class '__main__.BTreeNode'>":
        #if str(type(data)) != "<class 'py_btrees.btree_node.BTreeNode'>":
            raise ValueError(f"You can only write BTreeNodes to the disk, not {str(type(data))}.")
        if (addr >= len(self.memory)):
            raise ValueError(f"Error: Memory address {addr} has not yet been allocated. You cannot write to it.")
        block = pickle.dumps(data)
        #if len(block) > BLOCK_SIZE:
            #raise Exception(f"Data blob of size {len(block)} cannot fit in the block size of {BLOCK_SIZE}")
        if LOGGING:
            print(f"wrote {data} to block {addr}")
        self.memory[addr] = bytearray(block)

DISK = Disk()

__all__ = ["DISK", "LOGGING"]

KT = TypeVar("KT")  # Key Type for generics
VT = TypeVar("VT")  # Value Type for generics


class BTreeNode(Generic[KT, VT]):
    def __init__(self, my_addr: Address, parent_addr: Optional[Address], index_in_parent: Optional[int], is_leaf: bool):
        """
        Create a new BTreeNode. You do not need to edit this class at all, but you can. Be sure to leave the following attributes:

        * my_addr stores the address of this object (self)
          In other words, given a node address a, a == get_node(a).my_addr.

        * parent_addr stores the address of the parent node.

        * index_in_parent stores the location of this node in the parent's key list
          For example, if the parent has children [c1, c2, c3], then c1 should have
          index_in_parent == 0, c2 should have it 1, etc.

        * is_leaf keeps track of if this node is a leaf node or not.

        * keys stores the keys that this node uses to index, sorted ascending.
          If self.is_leaf, then foreach index i over range(len(keys)),
        * self.data[i] contains the data element for a key keys[i]
        * Likewise, if not self.is_leaf, then self.children_addrs[i]
          contains the address of a child node whose keys fall between
          keys[i-1] and keys[i] according to BTree rules.
          You can have each key represent either the max value of the left child
          or the min value of the right child.


        For instance, if keys = [10, 20, 30, 40]:
         children_addrs[0] should point to another node whose keys are all less than 10.
         children_addrs[1] should point to another node whose keys are all between 10 and 20.
         children_addrs[2] should point to another node whose keys are all between 20 and 30.
         children_addrs[3] should point to another node whose keys are all between 30 and 40.
         children_addrs[4] should point to another node whose keys are all greater than 40.
        Where "point to" means storing the address of that node.
        """
        self.my_addr = my_addr
        self.parent_addr = parent_addr
        self.index_in_parent = index_in_parent
        self.is_leaf = is_leaf
        self.keys: List[KT] = []
        self.children_addrs: List[Address] = []  # for use when self.is_leaf == False. Otherwise it should be empty.
        self.data: List[VT] = []  # for use when self.is_leaf == True. Otherwise it should be empty.
        self.next = None

    def get_child(self, idx: int) -> BTreeNode:
        return DISK.read(self.children_addrs[idx])

    def get_parent(self) -> BTreeNode:
        return DISK.read(self.parent_addr)

    def write_back(self):
        DISK.write(self.my_addr, self)

    #test
    def find_idx_child(self, current_children, child_key, child_adr):
        temp = list()
        for i in current_children:
            temp.append(DISK.read(i).keys[0])
        # temp1 = DISK.read(child)
        # temp2.keys[0]
        return bisect.bisect_left(temp,child_key)
    def insert_child(self, child_key, child_adr):
        if not self.children_addrs:
            self.children_addrs.append(child_adr)
        else:
            idx = self.find_idx_child(self.children_addrs, child_key, child_adr)
            self.children_addrs.insert(idx, child_adr)

    #test2
    def insert_idx_in_parent(self, parent):
        #temp = DISK.read(parent).children_addrs
        temp = parent.children_addrs
        for idx, child in enumerate(temp):
            if child == self.my_addr:
                self.index_in_parent = idx
                break

    def insert_idx_in_parent2(self, node):
        childre
        for idx, child in enumerate(DISK.read(node).children_addrs):
            if child == self.my_addr:
                self.index_in_parent = idx



    def find_idx(self, key: KT) -> Optional[int]:
        """
        Finds the index in self.keys where `key`
        should go, if it were inserted into the keys list.

        Assumes the keys array is sorted. Works in logarithmic time.
        """
        # Get index of key
        return bisect.bisect_left(self.keys,
                                  key)  # finds the insertion point for an item in a sorted list, or the spot just left of any matches

    def find_data(self, key: KT) -> Optional[VT]:
        """
        Given a key, retrieve the data associated with that key.
        Returns None if key is not present in self.keys.
        Only valid on leaf nodes.

        Works in logarithmic time using find_idx.
        """
        assert self.is_leaf
        idx = self.find_idx(key)
        # We can use the index we would insert at, and check if that entry has the key we need
        if idx < len(self.keys) and self.keys[idx] == key:
            return self.data[idx]
        return None

    def insert_data(self, key: KT, value: VT):
        """
        Insert the (key, value) pair into this leaf node.
        Preserves self.keys being sorted.
        Overwrites existing values with the same key.
        """
        assert self.is_leaf
        idx = self.find_idx(key)
        if idx < len(self.keys) and self.keys[idx] == key: ##this is when its a duplicate key
            self.data[idx] = value #updates value
        else: #if not duplicate
            self.keys.insert(idx, key)
            self.data.insert(idx, value)


# You may find this helper function useful
def get_node(addr: Address) -> BTreeNode:
    return DISK.read(addr)


class BTree:
    def __init__(self, M: int, L: int):
        """
        Initialize a new BTree.
        You do not need to edit this method, nor should you.
        """
        self.root_addr: Address = DISK.new() # Remember, this is the ADDRESS of the root node
        # DO NOT RENAME THE ROOT MEMBER -- LEAVE IT AS self.root_addr
        DISK.write(self.root_addr, BTreeNode(self.root_addr, None, None, True))
        self.M = M # M will fall in the range 2 to 99999
        self.L = L # L will fall in the range 1 to 99999
    #test
    def insert_idx_in_parent_check(self, node):
        if node is None:
            return
        node_children = DISK.read(node).children_addrs
        for idx, child in enumerate(node_children):
            new_node = DISK.read(child)
            new_node.index_in_parent = idx
            DISK.write(child, new_node)
        self.insert_idx_in_parent_check()


    def insert(self, key: KT, value: VT) -> None:
        leaf_node_adr = self.find_node(key)
        if not DISK.read(leaf_node_adr).keys:
            temp = DISK.read(leaf_node_adr)
            temp.keys.append(key)
            temp.data.append(value)
            DISK.write(leaf_node_adr, temp)
        else:
            temp = DISK.read(leaf_node_adr)
            temp.insert_data(key, value)
            DISK.write(leaf_node_adr, temp)
        if len(DISK.read(leaf_node_adr).keys) == self.M:
            self.split(DISK.read(leaf_node_adr), leaf_node_adr)


    def split(self, node, adr):
        median = math.ceil(self.M / 2) - 1
        # median = math.ceil(self.M / 2)
        right_node_adr = DISK.new()
        right_node = BTreeNode(right_node_adr, None, None, True)
        # right_node.keys = node.keys[median + 1:]
        right_node.keys = node.keys[median:]
        # right_node.data = node.data[median + 1:]
        right_node.data = node.data[median:]
        right_node.next = node.next
        left_node = BTreeNode(node.my_addr, None, None, True)
        # left_node.keys = node.keys[:median+1]
        left_node.keys = node.keys[:median]
        # left_node.data = node.data[:median+1]
        left_node.data = node.data[:median]
        left_node.next = right_node.my_addr
        self.add_to_parent(node, left_node, right_node.keys[0], right_node)



        # left_node_adr = DISK.new()
        # # DISK.write(left_node_adr, BTreeNode(left_node_adr, node.parent_addr, None, True))
        # median = math.ceil(self.M/2) -1
        # left_node = BTreeNode(left_node_adr, node.my_addr, None, True)
        # left_node.keys = node.keys[:median+1]
        # left_node.data = node.data[:median+1]
        # # left_node.next = adr
        # DISK.write(left_node_adr, left_node)
        # # right_node_adr = DISK.new() #might want to move this adr creation to later
        # right_node = BTreeNode(right_node_adr, node.my_addr, None, True)
        # right_node.keys = node.keys[median+1:]
        # right_node.data = node.data[median + 1:]
        # left_node.next = right_node_adr
        # right_node.next = node.next
        # self.add_to_parent(node, left_node, right_node.key[0], right_node)

    def add_to_parent(self, node, left_node, midkey, right_node):
        if node.my_addr == self.root_addr:
            self.root_addr = DISK.new()
            DISK.write(left_node.my_addr, left_node)
            DISK.write(right_node.my_addr,right_node)
            new_root_node = BTreeNode(self.root_addr, node.parent_addr, None, False)
            new_root_node.keys = [midkey]
            # new_root_node.children_addrs = [left_node.my_addr, right_node.my_addr]
            new_root_node.insert_child(DISK.read(left_node.my_addr).keys[0], left_node.my_addr)
            new_root_node.insert_child(DISK.read(right_node.my_addr).keys[0], right_node.my_addr)
            DISK.write(self.root_addr, new_root_node)
            left_node.parent_addr = new_root_node.my_addr
            # left_node.index_in_parent = 0 #might want to do an insert index_in_parent function that inserts
            test = DISK.read(new_root_node.my_addr)
            left_node.insert_idx_in_parent(test)
            # test = DISK.read(new_root_node.my_addr)
            DISK.write(left_node.my_addr, left_node)
            # right_node.index_in_parent = 1
            right_node.parent_addr = new_root_node.my_addr
            right_node.insert_idx_in_parent(test)
            DISK.write(right_node.my_addr, right_node)
            return


            # right_node_adr = DISK.new()
            # DISK.write(right_node_adr, right_node)
            # new_root_node = BTreeNode(self.root_addr, node.parent_addr, None, False)
            # new_root_node.keys = [midkey]
            # new_root_node.children_addrs = [left_node.my_addr, right_node.my_addr]
            # DISK.write(self.root_addr, new_root_node)
            # left_node.index_in_parent = 0
            # right_node.index_in_parent = 1
            # return
        else:
            upnode_adr = node.parent_addr
            upnode = DISK.read(upnode_adr)
            idx_in_parent = upnode.find_idx(midkey) #not using the insert data because I dont want data at this nonleaf node
            # old_upnode_keys = upnode.keys
            # old_upnode_keys.insert(idx_in_parent, midkey)
            upnode.keys.insert(idx_in_parent,midkey)
            # upnode.keys = old_upnode_keys.insert(idx_in_parent, midkey)
            # upnode.insert_child(left_node.my_addr) #redundant
            # test = DISK.read(right_node.my_addr).keys[0]
            DISK.write(right_node.my_addr, right_node)
            upnode.insert_child(DISK.read(right_node.my_addr).keys[0], right_node.my_addr)
            DISK.write(upnode_adr, upnode)
            # upnode.insert_child(test, right_node.my_addr)
            left_node.parent_addr = upnode.my_addr
            test = DISK.read(left_node.parent_addr)
            left_node.insert_idx_in_parent(test)
            DISK.write(left_node.my_addr, left_node)
            right_node.parent_addr = upnode.my_addr
            right_node.insert_idx_in_parent(test)
            DISK.write(right_node.my_addr, right_node)
            # n_children = DISK.read(upnode).children_addrs
            # len_children = len(n_children)
            # if len_children > self.M:
            if len(DISK.read(upnode.my_addr).children_addrs) > self.M:
                parent_right_node_adr = DISK.new()
                parent_right_node = BTreeNode(parent_right_node_adr, upnode.parent_addr, None, False)
                # median = math.ceil(self.M / 2) - 1
                median = math.ceil(self.M / 2) - 1
                # parent_right_node.keys = upnode.keys[median + 1:]
                parent_right_node.keys = upnode.keys[median+1:]
                # parent_right_node.children_addrs = upnode.children_addrs[median+1:]
                parent_right_node.children_addrs = upnode.children_addrs[median+1:]
                midpoint = upnode.keys[median]
                if median == 0:
                    # upnode.keys = upnode.keys[:median+1]
                    upnode.keys = upnode.keys[:median+1]
                else:
                    # upnode.keys = upnode.keys[:median]
                    upnode.keys = upnode.keys[:median]
                # upnode.children_addrs = upnode.children_addrs[:median+1]
                upnode.children_addrs = upnode.children_addrs[:median+1]
                DISK.write(parent_right_node.my_addr, parent_right_node)
                DISK.write(upnode.my_addr, upnode)
                for child in upnode.children_addrs:
                    temp = DISK.read(child)
                    temp.parent_addr = upnode.my_addr
                    test = DISK.read(upnode.my_addr)
                    temp.insert_idx_in_parent(test)
                    DISK.write(child,temp)
                for child in parent_right_node.children_addrs:
                    temp = DISK.read(child)
                    temp.parent_addr = parent_right_node.my_addr
                    test = DISK.read(parent_right_node.my_addr)
                    temp.insert_idx_in_parent(test)
                    DISK.write(child, temp)
                self.add_to_parent(upnode,upnode, midpoint, parent_right_node)



        # if self.keys

        """
        Insert the key-value pair into your tree.
        It will probably be useful to have an internal
        _find_node() method that searches for the node
        that should be our parent (or finds the leaf
        if the key is already present).

        Overwrite old values if the key exists in the BTree.

        Make sure to write back all changes to the disk!
        """
        # pass
    def find_node(self, key) -> leafnode:
        current_node = DISK.read(self.root_addr)
        while current_node.is_leaf is not True:
            nodekeys = current_node.keys
            len_keys = len(nodekeys)
            for i,j in enumerate(nodekeys):
                if key == j:
                    current_node = DISK.read(current_node.children_addrs[i+1])
                    break
                if key >j and int(len_keys -i) > 1:
                    if key < nodekeys[i+1]:
                        current_node = DISK.read(current_node.children_addrs[i+1])
                        break
                    elif key >= nodekeys[i+1]:
                        continue
                if key >j and int(len_keys-i) <= 1:
                    current_node = DISK.read(current_node.children_addrs[i+1])
                    break
                if key <j:
                    current_node = DISK.read(current_node.children_addrs[i])
                    break
        return current_node.my_addr



            # for child in rangecurrent_node

    def find(self, key: KT) -> Optional[VT]:
        node = DISK.read(self.find_node(key))
        return node.find_data(key)

        """
        Find a key and return the value associated with it.
        If it is not in the BTree, return None.

        This should be implemented with a logarithmic search
        in the node.keys array, not a linear search. Look at the
        BTreeNode.find_idx() method for an example of using
        the builtin bisect library to search for a number in
        a sorted array in logarithmic time.
        """
        # pass



a = BTree(5,5)
a.insert(1,2)
a.insert(2,3)
a.insert(3,4)
a.insert(4,5)
a.insert(5,6)
a.insert(6,7)
a.insert(7,8)
a.insert(8,9)
a.insert(9,10)
a.insert(10,11)
a.insert(11,12)
a.insert(12,13)
a.insert(13,14)
a.insert(14,15)
a.insert(15,16)
a.insert(16,17)
a.insert(17,18)
a.insert(18,19)
a.insert(19,20)


def printBtree(btree):
    root_node = DISK.read(btree.root_addr)
    print(root_node.keys)
    print('-----------------')
    # while root_node is not None:
    for i in root_node.children_addrs:
        print('-----------------')
        print(DISK.read(i).keys)
        print('-----------------')
        for j in DISK.read(i).children_addrs:
            # print(DISK.read(i).keys)
            print(DISK.read(j).keys)
    print('-----------------')
    # leftchild =

printBtree(a)
    # root = DISK.read


a.find(1)
a.find(2)
a.find(3)
a.find(4)
a.find(5)
a.find(6)
a.find(7)
a.find(8)
a.find(9)
a.find(10)
a.find(11)
a.find(12)
a.find(13)
a.find(14)
a.find(15)
a.find(16)
a.find(17)
a.find(18)





# d = DISK.read(b)
# DISK.memory[0]
# c = pickle.loads(DISK.memory[0])
#
# a = BTree(3,3)
# b = a.root_addr
# b
# a = DISK.new()
# b = DISK.new()
# DISK.new()
# DISK.read(a)

# if not DISK.memory:
#     print("nothing")
# else:
#     print("caca")



a = [3,4,5,2,43,6]

for i in range(len(a)):
    for j in range(i-1):
        print (j)

