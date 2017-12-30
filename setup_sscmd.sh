#download new python
wget https://www.python.org/ftp/python/2.7.13/Python-2.7.13.tar.xz
tar -xvf Python-2.7.13.tar.xz

#install gcc and required packages
yum install gcc -y
yum install readline-devel.x86_64 -y
yum install zlib-devel -y
yum -y install openssl openssl-devel
yum -y install sqlite-devel

#install new python
cd Python-2.7.13
./configure --with-readline --with-zlib=/usr/include --enable-unicode=ucs4
make
make install
cd ..

#intall new pip
yum remove python-pip -y
wget https://bootstrap.pypa.io/get-pip.py
python get-pip.py

#install git
yum install git -y

#install twisted
git https://github.com/twisted/twisted.git
cd twisted
python setup.py install

#install pytz 
pip install pytz

#install django
pip install django


