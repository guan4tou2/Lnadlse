1. 攻擊原理  
Slowloris是Dos攻擊的一種，原理是以極低的速度往server發送HTTP請求，並在HTTP Headers只傳送一組的\r\n讓server認為Header的部分還沒結束，因此保持著連線不中斷，繼續等待完整的請求，進而占用server可允許的連接數使其達到上限不再接受新的連線。  
2. 操作方式  
安裝python: `sudo apt-get install python3`  
安裝gitclone:`sudo apt-get install curl`  
下載slowloris攻擊python檔案:` curl -O https://raw.githubusercontent.com/guan4tou2/Lnadlse/main/Attacks/DoS/slowloris.py`  
本專題使用之Slowloris攻擊程式為原作者提供之程式碼並由Hox Framework所修改的版本，僅需更改Slowloris的Python程式內howmany_sockets、ip及port的內容即可。  
howmany_sockets為設定要多少的連線數，ip為要攻擊的server IP，port為該server有開啟的port，預設為80 port。  
3. 特徵  
遭受到Slowloris攻擊的server最明顯的特徵為連接數的大量增加，其次可能出現server的回應中request timeout的大量增加以及大量且單一的GET請求等等。  
