echo "Cloning Repo...."
if [ -z $BRANCH ]
then
  echo "Cloning main branch...."
  git clone https://github.com/Kuchbhiarfk/Fwock Kuchbhiarfk/Fwock 
else
  echo "Cloning $BRANCH branch...."
  git clone https://github.com/Kuchbhiarfk/Fwock -b $BRANCH /Fwock
fi
cd Kuchbhiarfk/Fwock 
pip3 install -U -r requirements.txt
echo "Starting Bot...."
gunicorn app:app & python3 main.py
