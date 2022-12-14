# *************************************************************************
## CREATO DA ORTU prof. DANIELE
## daniele.ortu@itisgrassi.edu.it

# from danieleRSINK import tbk
import os
import ast
import subprocess
from datetime import datetime

CURRDIR = os.path.dirname(os.path.abspath(__file__))
NOME_FCONF = os.path.join(CURRDIR, 'danieleReteBK.conf')
NOME_FPAR = os.path.join(CURRDIR, 'comunica.conf')

DEBUG = False


class bkFile():
    # def __init__(self, ch, bks, cd):
    def _printa(self, s):
        if DEBUG:
            print(s)

    def __init__(self):
        self._path_fconf = NOME_FCONF
        self._path_fpar = NOME_FPAR
        self._bks, self._altro = self._get_impostazioni()

    def _is_running(self, ps):
        r = subprocess.run(["ps", "-e"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if r.stderr:
            print("\nERRORE: " + r.stderr.decode("utf-8"))
            return False
        l = r.stdout.decode("utf-8").split("\n")

        for ch in l:
            print(ch)
            if ps in ch:
                return True
        return False
        # print(ch)

    def _esegui(self, ch):
        self._printa("********************** Inizia thread: "+ch)
        self.__inizializza_backup(ch)
        self._flog.write("Variabili inizializzate")
        if self.__inizializza_paths():
            self.__backuppa()
        self._printa("********************** fine thread")

    def __inizializza_backup(self, ch):
        data = self._bks[ch]
        if DEBUG:
            self._printa(data)
        self._remotoDA = data['dirDA']["remoto"]
        self._remotoTO = data['dirTO']["remoto"]
        self._dirBASE = CURRDIR
        if self._remotoDA:
            self._protocolloDA = data['dirDA']["protocollo"]
            if self._protocolloDA=='sshfs':
                self._dirDA = data['dirDA']['utente'] +'@' + \
                    data['dirDA']["host"] + ":" + \
                    data['dirDA']["rem_path"]
            elif self._protocolloDA == 'smb':
                self._dirDA = "//" +  data['dirDA']["host"] + data['dirDA']["rem_path"]
        else:
            self._dirDA = data['dirDA']["loc_path"]
        if self._remotoTO:
            self._protocolloTO = data['dirTO']["protocollo"]
            if self._protocolloTO == 'sshfs':
                self._dirTO = data['dirTO']['utente'] + '@' + \
                    data['dirTO']["host"] + ":" + \
                    data['dirTO']["rem_path"]
            elif self._protocolloTO == 'smb':
                self._dirTO = "//" + data['dirTO']["host"] + data['dirTO']["rem_path"]
        else:
            self._dirTO = data['dirTO']["loc_path"]
        self._mntDA = data['dirDA']["mnt"]
        self._mntTO = data['dirTO']["mnt"]
        self._nome = ch
        self._path_flog = CURRDIR + "/" + self._nome + ".log"
        self._flog = open(self._path_flog, "w")
        self._do = datetime.today().strftime('%Y-%m-%d-%H-%M-%S')
        # self._latestDIR = self._dirTO + "/" + "latestDIR"
        self._latestDIR = CURRDIR + "/" + self._mntTO + "/" + "latestDIR"
        self._nomeStatoFile = "stf.bin"
        self.__nomeTAR = self._do + "-" + self._nome + ".tar.gz"

    def _monta(self, proto, dir,  mnt):
        self._flog.write("\nMonto con protocollo: " + proto)
        if proto == 'sshfs':
            r = subprocess.run([proto, dir, mnt],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if r.stderr:
                self.__log("\nERRORE: " + r.stderr.decode("utf-8"), True)
                self.initOK = False
                return False
        elif proto == 'smb':
            # mount -t cifs -o vers=1.0,username=uffici,password=77ykgUU //172.16.200.100/Volume_1 /mnt/NAS
            # para = 'vers=1.0,username=daniele,password=ortu'
            para = 'vers=2.0,username=daniele,password=ortu'
            print('mount -t cifs -o ' + para +' ' + dir + ' ' + mnt)
            r = subprocess.run(['mount', '-t', 'cifs', '-o', para, dir, mnt],
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if r.stderr:
                self.__log("\nERRORE: " + r.stderr.decode("utf-8"), True)
                self.initOK = False
                return False

    def __lastDir(self, rootdir):
        try:
            for file in os.listdir(rootdir):
                l = []
                d = os.path.join(rootdir, file)
                if os.path.isdir(d):
                    l.append(d)
            n = len(l)
            if n > 0:
                #return l.reverse()[0]
                return l[n-1]
            else:
                return "urka"
        except:
            print(rootdir)
            return "urkissima"

    def __inizializza_paths(self):

        # self._flog.write("\nMonto con protocollo: " + self._dirDA)
        if self._remotoDA:
            self._flog.write("\nMonto directory da backuppare: " + self._dirDA)
            mntDA = self._dirBASE + "/" + self._mntDA
            if not self.__isMount(self._dirDA):
                if not self._monta(self._protocolloDA, self._dirDA, mntDA):
                    self._flog.close()
                    return False
                self._flog.write("\nDirectory origine montata")
            else:
                self._flog.write("\nDirectory GIA montata")
            self._dirDA = mntDA
        if self._remotoTO:
            self._flog.write("\nMonto directory dei backup: " + self._dirTO)
            mntTO = self._dirBASE + "/" + self._mntTO
            if not self.__isMount(self._dirTO):
                if not self._monta(self._protocolloTO, self._dirTO, mntTO):
                    self._flog.close()
                    return False
                self._flog.write("\nDirectory di backup montata")
            else:
                self._flog.write("\nDirectory GIA montata")
            self._dirTO = mntTO

            self._latestDIR = self._latestDIR  + self._mntTO
        self._flog.write("\nFine inizializzazione processo")
        return True

    def _get_impostazioni(self):
        with open(self._path_fconf, "r") as data:
            d = ast.literal_eval(data.read())
            data.close()
        # d=MainW.get_impostazioni(self.fconf)
        return d['bks'], d['altro']

    def __isMount(self, sub):
        r = subprocess.run(["df"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return sub in str(r.stdout)

    def __log(self, msg, mail):
        self._flog.write(msg)
        self._flog.close()
        if mail and not DEBUG:
            dummy = 0
            m = "mail -s  '" + self._nome + "' server.backup@itisgrassi.edu.it < " + self._path_flog
            os.system(m)
            # print(m)
        self._printa("MAIL INVIATA: mail -s  '" + self._nome + "' server.backup@itisgrassi.edu.it < " + self._path_flog)

    def __backuppa(self):
        print("Inizio backup")
        self._flog.write("\n*********Inizio il processo di backup************")
        self._flog.write("\nUso come base: " + self._latestDIR)
        # attr = '-auv --link-dest "' + self._latestDIR + '" --exclude=".cache" '
        dirBK = self._dirTO + "/" + self._do + "-" + self._nome
        attr = '-auv --link-dest "' + self.__lastDir(self._dirTO) + '" --exclude=".cache" '
        rsync = "rsync " + attr + "\n\t" + self._dirDA + "/\n\t" + dirBK + "\n\t > " + self._path_flog
        self._flog.write("\n" + rsync)
        r = os.system("rsync " + attr + self._dirDA + "/ " + dirBK + " > " + self._path_flog)
        self._flog.close()
        self._flog = f = open(self._path_flog, "a")
        #self._flog.write("\nRimuovuo: " + self._latestDIR)
        #r = os.system("rm -rf " + self._latestDIR)
        #self._flog.write("\nNuova base: " + self._dirTO + "/" + self._do + "-" + self._nome)
        #self._flog.write(
        #    "\nCreo link: ln -s " + self._dirTO + "/" + self._do + "-" + self._nome + " " + self._latestDIR)
        # r = os.system("ln -s " + self._dirTO + "/" + self._do + "-" + self._nome + " " + self._latestDIR)
        #r = subprocess.run(["ln", "-s", self._dirTO + "/" + self._do + "-" + self._nome, self._latestDIR],
        #                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        #if r.stderr:
        #    self.__log("\nERRORE: " + r.stderr.decode("utf-8"), True)
        #    self.initOK = False
        #    return False

        self.__log("\nPROCESSO ESEGUITO CON SUCESSO\n\n", True)
        print("Finito backup")
        self._flog.close()


 # c = bkFile()
# c._esegui()
