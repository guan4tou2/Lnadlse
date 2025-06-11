import argparse
import os
import re

path=os.path.dirname(os.path.realpath(__file__))

TargetedList = "、".join(list(os.listdir(os.path.join(path, "Targeted")))).replace('、packetbeat','')
AttackerList = "、".join(list(os.listdir(os.path.join(path, "Attacker"))))

parser = argparse.ArgumentParser(prog="make", description="建立攻防環境模組安裝文件")
parser.add_argument("-T", "--Targeted", default="httpd",
                    type=str, help=f"請選擇靶機image名稱，有[{TargetedList}]")
parser.add_argument("-t", "--TargetedNum", default="1",
                    type=str, help=f"請選擇靶機數量")
parser.add_argument("-A", "--Attacker", default="kali-xrdp",
                    type=str, help=f"請選擇攻擊機image名稱，有[{AttackerList}]")
parser.add_argument("-a", "--AttackerNum", default="1",
                    type=str, help=f"請選擇靶機數量")

args = parser.parse_args()
print(args)
try:
    if args.Targeted not in TargetedList.split('、'):
        raise Exception(f"Targeted '{args.Targeted}' 不存在，請重新選擇{TargetedList}")
    if args.Attacker not in AttackerList.split('、'):
        raise Exception(f"Attacker '{args.Attacker}' 不存在，請重新選擇{AttackerList}")
    targetednum = int(args.TargetedNum)
    attackernum = int(args.AttackerNum)

    #docker compose
    with open(os.path.join(path, 'docker-compose-example.yml'), 'r',encoding="utf-8") as f:
        yml = f.read()
    targeted = re.search(
        r"#targeted start\n  ([:\w\n \-'_#\"\d]*)  #targeted end",  yml).group(1)
    attacker = re.search(
        r"#attacker start\n  ([:\w\n \-'_#\"\d/\.]*)  #attacker start",  yml).group(1)
    yml=re.sub(targeted,"#targeted#\n",yml)
    yml=re.sub(attacker,"#attacker#\n",yml)
    targeted = re.sub(r"targeted", args.Targeted, targeted)
    attacker = re.sub(r"attacker", args.Attacker, attacker)

    #makefile
    with open(os.path.join(path, 'makefile-example'), 'r',encoding="utf-8") as f:
        makefile = f.read()
    makefile = re.sub(r'targeted', args.Targeted, makefile)
    makefile = re.sub(r'attacker', args.Attacker, makefile)
    
    Targeted = "".join([re.sub(r"num", str(i+1), targeted) for i in range(targetednum)])
    Attacker = "".join([re.sub(r"num", str(i+1), attacker)
                       for i in range(attackernum)])
    Make = "".join([f'\tdocker exec `docker ps -aqf "name=Targeted-{i+1}"` "make"\n' for i in range(targetednum)])
    makefile = re.sub(
        r'\tdocker exec `docker ps -aqf "name=Targeted-num"` "make"', Make, makefile)
    yml = re.sub(r"#targeted#\n", Targeted, yml)
    yml = re.sub(r"#attacker#\n", Attacker, yml)

    with open(os.path.join(path, 'docker-compose.yml'), 'w',encoding="utf-8") as f:
        f.write(yml)
    with open(os.path.join(path, 'makefile'), 'w',encoding="utf-8") as f:
        f.write(makefile)
    print(
        f"攻防環境模組已生成。\n\t攻擊機: {args.Attacker:15}x {args.AttackerNum}\n\t靶機  : {args.Targeted:15}x {args.TargetedNum}")
except Exception as msg:
    print("攻防環境模組設置錯誤，錯誤原因:",msg)
