# coding=utf-8


import csv
import re
import sys
import getopt
import codecs, cStringIO


class TransactionTable:
  """ A simple class representing a 2D table, can be filled from CSV and written back to CSV. Furthermore it offers several ways of transforming the data in the table. """
  def __init__(self):
    self.columns = []
    self.data = []
    
  def from_csv(self, handle, delimiter=',', encoding="utf-8"):
    
    csv_reader = UnicodeReader(handle, delimiter=delimiter, encoding=encoding)
    
    i=0
    for row in csv_reader:
      if i==0:
        self.columns = [c.strip().replace(' ','_') for c in row]
      else:
        self.data.append(row)
      i += 1
      print "imported line %d " % i 
  
  def display(self, columns = None, column_width = 10):

    cw = u"{0:>"+str(column_width)+"}"
    
    if columns == None:
      columns = self.columns
      data = self.data
    else:
      data = self.collect_columns(columns)
    
    for h in columns:
      sys.stdout.write( " | "+ cw.format(unicode_cell(h)[:column_width]) )
    sys.stdout.write("\n")
    for row in data:
      for c in row:
        cstr = cw.format(unicode_cell(c)[:column_width])
        sys.stdout.write(" | "+cstr.encode("utf-8") )
      sys.stdout.write("\n")
      
  
  def to_csv(self, handle, columns=None, encoding="utf-8"):
    """ returns a CSV string representation of the table, by default all columns are represented.  If an array of column names is given, only these will be represented in the given order. """
    
    csv_writer = UnicodeWriter(handle, delimiter=',', encoding=encoding, quotechar='"', quoting=csv.QUOTE_MINIMAL)
    
    if columns == None:
      # write column headers
      csv_writer.writerow(self.columns)
      # write all rows
      csv_writer.writerows(self.data)
    else:
      csv_writer.writerow(columns)
      csv_writer.writerows( self.collect_columns(columns) )
    
    
  ################
  
  def reverse(self):
    self.data.reverse()
  
  def map_column(self, name, mapping):
    """ update all values of the column identified by 'name' to  mapping(original_cell_value) """
    idx = self.columns.index(name)
    _data = []
    for row in self.data:
      row[idx] = mapping(row[idx])
      _data.append(row)
      
    self.data = _data

  def update_column(self, name, values):
    """ update all values of the column identified by 'name' to the corresponding item in values """
    idx = self.columns.index(name)
    _data = []
    for i,row in enumerate(self.data):
      row[idx] = values[i]
      _data.append(row)
      
    self.data = _data
  


  def add_column(self, name, values):
    _data = []
    col_len =len(self.columns)
    self.columns.append(name)
    for ix, row in enumerate(self.data):
      while len(row)<col_len:
        row.append(None)
      if len(row) != col_len:
        raise Exception('Row length does not match number of columns')
      row.append(values[ix])
      _data.append(row)
      
    self.data = _data
    
    
  
    
    
  def map_rows(self, mapping):
    """ update all rows to  mapping(oldrow)     mapping expects a dict of columnname => value  as input and should also produce a similar dict as output """
    c,d = self._map_rows( mapping, self.columns, self.dictdata() )
    self.data = d
    self.columns = c
    
  def _map_rows(self, mapping, columns, dictdata):
    _data = []
    _columns = columns
    for rowdict in  dictdata:
      newrowdict = mapping(rowdict)
      
      newrow = [None] * len(_columns)
      for k,v in newrowdict.iteritems():
        try:
          ix = _columns.index(k)
          newrow[ix] = v
        except ValueError:
          # create a new column for this field
          _columns.append(k)
          newrow.append(v)
      _data.append(newrow)
    return _columns, _data
    
  def add_dict_rows(self, dictrows):
    def identity(x):
      return x
    c,d = self._map_rows( identity, self.columns, dictrows )
    self.columns = c
    
    for row in d:
      self.data.append(row)
    
    
  def filter_rows(self, condition):
    """ removes all rows for which condition(row) returns False """
    _data = []
    for row in self.data:
      rowdict = dict( zip(self.columns,row) )
      if condition(rowdict):
        _data.append(row)
      
    self.data = _data
    
    
  def collect_columns(self, names):
    """ return a list of rows, with each row only containing those columns identified by 'names' ordered like 'names' """
    idxs = [] 
    for name in names:
      try:
        idxs.append( self.columns.index(name) )
      except:
        idxs.append( None )
    
    data = [ [ row[ix] if ix != None and ix <len(row) else None for ix in idxs ] for row in self.data]
    
    return data
    
    
  def collect_column(self, name):
    """ return all values of the column identified by 'name' """
    idx = self.columns.index(name)
    
    values = [row[idx] for row in self.data]
    
    return values
    
    
  def produce_table(self, producer):
    newtable = TransactionTable()
    _columns = []
    _data = []
    for rowdict in self.dictdata():
      newrows = producer(rowdict)
      newtable.add_dict_rows(newrows)
    return newtable
      
      
  def dictdata(self):
    _data = []
    for row in self.data:
      rowdict = dict( zip(self.columns, row) )
      _data.append(rowdict)
    return _data

##########################
##########################

    
def unicode_cell(obj):
  if obj == None:
    return u''
  else:
    return unicode(obj)
    
    
      
# taken from http://docs.python.org/library/csv.html      
    
class UTF8Recoder:
    """
    Iterator that reads an encoded stream and reencodes the input to UTF-8
    """
    def __init__(self, f, encoding):
        self.reader = codecs.getreader(encoding)(f)

    def __iter__(self):
        return self

    def next(self):
        return self.reader.next().encode("utf-8")
    
    
class UnicodeReader:
    """
    A CSV reader which will iterate over lines in the CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        f = UTF8Recoder(f, encoding)
        self.reader = csv.reader(f, dialect=dialect, **kwds)

    def next(self):
        row = self.reader.next()
        return [unicode(s, "utf-8") for s in row]

    def __iter__(self):
        return self
        
        
class UnicodeWriter:
    """
    A CSV writer which will write rows to CSV file "f",
    which is encoded in the given encoding.
    """

    def __init__(self, f, dialect=csv.excel, encoding="utf-8", **kwds):
        # Redirect output to a queue
        self.queue = cStringIO.StringIO()
        self.writer = csv.writer(self.queue, dialect=dialect, **kwds)
        self.stream = f
        self.encoder = codecs.getincrementalencoder(encoding)()

    def writerow(self, row):
        self.writer.writerow([unicode_cell(s).encode("utf-8") for s in row])
        # Fetch UTF-8 output from the queue ...
        data = self.queue.getvalue()
        data = data.decode("utf-8")
        # ... and reencode it into the target encoding
        data = self.encoder.encode(data)
        # write to the target stream
        self.stream.write(data)
        # empty queue
        self.queue.truncate(0)

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)
