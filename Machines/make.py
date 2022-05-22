import argparse
import sys
import os
import re

path=os.path.dirname(os.path.realpath(__file__))

targeter_list = "、".join(list(os.listdir(os.path.join(path, "Targeter")))).replace('、packetbeat','')
attacker_list = "、".join(list(os.listdir(os.path.join(path, "Attacker"))))
# attacks_list="、".join(list(map(removefile,os.listdir(os.path.join(os.getcwd(),"Attacks")))))
# beat_list="、".join(list(map(removefile,os.listdir(os.path.join(os.getcwd(),"Beat")))))

parser = argparse.ArgumentParser(prog="make", description="建立攻防環境模組安裝文件")
parser.add_argument("-T", "--Targeter", default="httpd",
                    type=str, help=f"請選擇靶機image名稱，有[{targeter_list}]")
parser.add_argument("-A", "--Attacker", default="kali",
                    type=str, help=f"請選擇攻擊機image名稱，有[{attacker_list}]")
# parser.add_argument("-a", "--Attack",default="Dos", type=str, help=f"請選擇攻擊方式，有[{attacks_list}]")
# parser.add_argument("-B", "--Beat",default="packetbeat", type=str,help=f"請選擇要安裝於靶機上的beat，有{beat_list}")
args = parser.parse_args()

try:
    if args.Targeter not in targeter_list.split('、'):
        raise Exception(f"Targeter '{args.Targeter}' 不存在，請重新選擇{targeter_list}")
    if args.Attacker not in attacker_list.split('、'):
        raise Exception(f"Attacker '{args.Attacker}' 不存在，請重新選擇{attacker_list}")
    # if args.Attack not in attacks_list.split('、'):print(f"Attack '{args.Attack}' 不存在，請重新選擇{attacks_list}")
    # if args.Beat not in beat_list.split('、'):print(f"Beat '{args.Beat}' 不存在，請重新選擇{beat_list}")

    with open(os.path.join(path, 'docker-compose.yml'), 'r') as f:
        yml = f.read()
        result = re.finditer(r"image: '\w{8}_(\S*)'",  yml)
        machines = []
        for _ in result:
            machines.append(_.groups()[0])
        yml = re.sub(machines[0], args.Targeter, yml)
        yml = re.sub(machines[1], args.Attacker, yml)
    with open(os.path.join(path, 'makefile'), 'r') as f:
        makefile = f.read()
        result = re.finditer(r"[A-Z]\w{7}\/(\S*)",  makefile)
        machines = []
        for _ in result:
            machines.append(_.groups()[0])
        makefile = re.sub(machines[0], args.Targeter, makefile)
        makefile = re.sub(machines[1], args.Attacker, makefile)
        makefile = re.sub(machines[2], args.Attacker, makefile)
        makefile = re.sub(machines[3], args.Attacker, makefile)

    with open(os.path.join(path, 'docker-compose.yml'), 'w') as f:
        f.write(yml)
    with open(os.path.join(path, 'makefile'), 'w') as f:
        f.write(makefile)
    print(f"攻防環境模組已設置完成，攻擊機: {args.Targeter} ，靶機: {args.Attacker} ")
except Exception as msg:
    print("攻防環境模組設置錯誤，錯誤原因:",msg)
