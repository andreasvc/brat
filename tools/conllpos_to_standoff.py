"""Convert POS tags in CoNLL-2012 files to standoff.

Usage: convert.py <conlldir> <tokdir> <outputdir>

Where <conlldir> contains .conll files, <tokdir> contains .txt files with
tokenized text. This script will create (and overwrite!)
.txt and .ann files in <outdir>, segmented into chunks of about 2000 tokens."""
import os
import sys
from glob import glob


def readconll(conllfile):
	"""Read conll data as dict of list of lists.

	i.e., conlldocs[docname][sentno][tokenno][col]
	Adds orignal line number as first column."""
	conlldocs = {}
	lineno = 0  # 1-indexed line numbers
	with open(conllfile) as inp:
		while True:
			line = inp.readline()
			lineno += 1
			if line.startswith('#begin document '):
				docname = line.strip().split(' ', 2)[2]
				conlldocs[docname] = [[]]
				while True:
					line = inp.readline()
					lineno += 1
					if line.startswith('#end document') or line == '':
						break
					elif line.startswith('#'):
						pass
					elif line.strip():
						conlldocs[docname][-1].append(
							[lineno] + line.strip().split())
					else:
						conlldocs[docname].append([])
				# remove empty sentence if applicable
				if not conlldocs[docname][-1]:
					conlldocs[docname].pop()
				if not conlldocs[docname]:
					raise ValueError('docname %r of conll file %r is empty' % (
							docname, conllfile))
			elif line == '':
				break
	if not conlldocs:
		raise ValueError('Could not read conll file %r' % conllfile)
	return conlldocs


def tokstr(start, end, ttype, idnum, text):
	# sanity checks
	if '\n' in text:
		raise ValueError('newline in entity %r' % text)
	if text != text.strip():
		raise ValueError('tagged span contains extra whitespace: %r' % text)
	return 'T%d\t%s %d %d\t%s' % (idnum, ttype, start, end, text)


def main():
	try:
		_, conlldir, tokdir, outdir = sys.argv
	except ValueError:
		print(__doc__)
	for fname in glob(os.path.join(tokdir, '*.txt')):
		print('processing:', fname)
		name = os.path.splitext(os.path.basename(fname))[0]
		conlldata = readconll(os.path.join(conlldir, name + '.conll'))
		if len(conlldata) != 1:
			raise ValueError('expected a single documment per conll file')
		conlldata = next(iter(conlldata.values()))
		with open(os.path.join(tokdir, name + '.txt')) as inp:
			tokenized = [line.replace('|', ' ', 1).split(' ')
					for line in inp.read().splitlines()]
		if len(conlldata) != len(tokenized):
			raise ValueError('mismatch in number of sentences')
		segment = 1
		out = open(os.path.join(outdir, '%s_%02d.ann' % (name, segment)), 'w')
		out2 = open(os.path.join(outdir, '%s_%02d.txt' % (name, segment)), 'w')
		idnum = 1
		offset = 0
		for conllsent, toksent in zip(conlldata, tokenized):
			if len(conllsent) != len(toksent[1:]):
				for line in conllsent:
					print(line)
				print(toksent)
				raise ValueError('mismatch in sentence length')
			offset += len(toksent[0]) + 1
			for conlltok, tok in zip(conllsent, toksent[1:]):
				pos = conlltok[5]
				pos = pos[:pos.index('[')]
				text = conlltok[4]
				print(tokstr(offset, offset + len(text), pos, idnum, text),
						file=out)
				offset += len(text) + 1
				idnum += 1
			print(' '.join(toksent).replace(' ', '|', 1), file=out2)
			if idnum >= 1000:
				out.close()
				out2.close()
				segment += 1
				idnum = 1
				offset = 0
				out = open(os.path.join(
						outdir, '%s_%02d.ann' % (name, segment)), 'w')
				out2 = open(os.path.join(
						outdir, '%s_%02d.txt' % (name, segment)), 'w')
		out.close()
		out2.close()


if __name__ == '__main__':
	main()
