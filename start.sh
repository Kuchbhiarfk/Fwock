echo "Cloning Repo...."
if [ -z $BRANCH ]
then
  echo "Cloning main branch...."
  git clone https://github.com/Sethijai/Forwards Sethijai/Forwards 
else
  echo "Cloning $BRANCH branch...."
  git clone https://github.com/Sethijai/Forwards -b $BRANCH /Forwards
fi
cd Sethijai/Forwards 
pip3 install -U -r requirements.txt
echo "Starting Bot...."
gunicorn app:app & python3 main.py
