import os
import shutil

def ls (dirpath, selector) :
	s = [];
	for p in os.listdir(dirpath) :
		if selector(p) :
			s.append(p)
	return s

def cp (sr, tr, dn, selector) :
	if dn : os.makedirs(os.path.join(tr,dn), exist_ok=True)
	(s,t) = (os.path.join(sr,dn), os.path.join(tr,dn)) if dn else (sr,tr)
	for f in ls(s, selector ) :
		print(f);
		shutil.copy2(os.path.join(s,f),t);

awd= os.path.realpath(os.path.join(os.path.dirname(__file__),'..'))
cp(awd, './', 'app', lambda fn : fn.endswith('.py'))
cp(awd, './', 'etc', lambda fn : fn.endswith('.json'))
cp(awd, './', None, lambda fn : fn.startswith('play.'))
