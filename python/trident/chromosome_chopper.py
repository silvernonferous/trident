#!/usr/bin/env python
"""
Breaks up chromosome files into arbitrarily smaller sizes

Requires an input sequence, an output file prefix and a 
chunk size (number of 70-character lines).
"""


def create_outfile_name(prefix,file_counter):
    return "%s-%d" % (prefix,file_counter)

def outfile_exists(prefix,file_counter):
    """
    Indictates wither or not the file that would be created already exists.

    @param prefix: File prefix
    @type prefix: str
    @param file_counter: Index of file being created
    @type file_counter: int
    @return: bool
    """
    from os.path import isfile
    return isfile(create_outfile_name(prefix,file_counter))

def open_outfile(prefix,file_counter):
    return open(create_outfile_name(prefix,file_counter) ,"w")

def create_header(old_header,chunksize,seq_size,header_map = {}):
    """
    Creates a fasta header line that contains information about the chromosome segment.
    
    @param old_header: Original header from chromosome.
    @type old_header: str
    @param chunksize: Size of segment
    @type chunksize: int
    @param seq_size: Total size of sequence
    @type seq_size: int
    @param header_map: Optional list of user defined header values. These override the values in the original fasta header.
    @type header_map: dict
    @return: Header string
    """
    import datetime
    import re
    from trident import FastaError
    
    
    header = ">"
    species = None
    if "species" in header_map:
        species = header_map['species']
    assembly = None
    if "assembly" in header_map:
        assembly = header_map['assembly']   

    # Construct the chromosome reference tag.
    # First, if the user provided it in the header_map dict, use that.
    # Otherwise, if "chromosome" is found in the header followed by a
    #    word characters, use that
    # Otherwise, if mitochondrion is found, use that.
    # Otherwise, label it as "UnknownSequenceType"
    if "chromosome" in header_map:
        header += "{0}|".format(header_map['chromosome'])
    elif "chromosome" in old_header:
        if not species:
            species = re.findall(r"\|\s*(\S*)\s*(\S*)\s*(strain|chromosome)",old_header)
            if not species:
                raise FastaError("Could not determine species name based"
                                 " on header. Try using the -s flag")
            species = species[0]
        m = re.findall(r"chromosome\s*(\w*)",old_header)
        if not m:
            raise FastaError("Missing chromosome label")
        header += "chr{0}|".format(m[0])
    elif old_header.find("mitochondrion"):
        if not species:
            species = re.findall(r"\|\s*(\S*)\s*(\S*)\s*(strain|mitochondrion)",old_header)
            species = species[0]
        header += "mitochondrion|";
    else:
        header+= "UnknownSequenceType|"
    header += "%s|" # to be filled in at file write
    header += r"%d|" # offset of segment in sequence, zero indexed
    header += "%d|" % seq_size # total sequence length
    header += str(chunksize) + "|"
    rightnow = datetime.date.today()
    header += rightnow.isoformat().replace('-','') + "|"
    if not assembly:
        m = re.findall(r"\s*(\S*) Primary Assembly",old_header)
        if len(m) == 0:
            assembly = "UnknownAssembly"
        else:
            assembly = m[0]
    header += assembly + "|"
    if not species or len(species[0]) < 2:
        raise FastaError("Missing species name. Received '{0}'".format(species))
    header += "[%s.%s]" % (species[0][0],species[1])
    return header + "\n"
    
def chopper(filename,prefix,chunk_size,overwrite = True, header_map = {}):
    """
    Opens the specified file and breaks it into 'chunk_size' number of lines.
    The results are placed in files, using the filename scheme prefix-index,
    where index is a zero-indexed value listing its position in the
    original file.

    @param filename: Name of file to segment
    @type filename: str
    @param prefix: File name prefix for segments.
    @type prefix: str
    @param chunk_size: Size of segments
    @type chunk_size: int  
    @param overwrite: Indicates whether files should be overwritten. If False, the files are left unmodified.
    @type overwrite: bool
    @return: Number of files produced
    """
    from trident import FastaError
    
    infile = open(filename,"r")

    header = infile.readline()
    if len(header) == 0 or header[0] != '>':
        raise FastaError("Improper Header")
                
    nchars = 0
    for line in infile:
        nchars += len(line.strip())
    infile.seek(0)
    infile.readline()
        
    header = create_header(header,chunk_size,nchars,header_map)

    file_counter = 1
    seq_offset = 0

    # Even if overwrite is True and we are not writing
    # to a file, we need to keep track of lines and file_counter 
    # values. So we need to turn writing on and off for each 
    # individual segment. This will be done using inhibit_writing
    inhibit_writing = False
    if not overwrite and outfile_exists(prefix,file_counter):
        inhibit_writing = True

    outfile = None
    if not inhibit_writing:
        outfile = open_outfile(prefix,file_counter)
        outfile.write(header % (file_counter,seq_offset))

    file_counter += 1
    counter = 1
    
    for line in infile:
        if counter > 0 and counter % chunk_size == 0:
            if not inhibit_writing:
                outfile.write(line)
                outfile.close()
            if not overwrite and outfile_exists(prefix,file_counter):
                inhibit_writing = True
            if not inhibit_writing:
                outfile = open_outfile(prefix,file_counter)
                outfile.write(header % (file_counter,seq_offset))
            file_counter += 1
            counter = 0
        if not inhibit_writing:
            outfile.write(line)
        seq_offset += len(line.strip())
        counter += 1

    if outfile:
        outfile.close()

    return file_counter-1

