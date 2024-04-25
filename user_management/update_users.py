import getpass
import sys
import os
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import time
import paramiko

# The first step is to classify your uid as Admin. Thus, it is not necessary to use sudo to perform sacctmgr modifications
# example: sudo sacctmgr add user jcss4 account=test_acc partition=long,short,test AdminLevel=Admin

def add_users(ssh_client):
	# define the scope
	scope = ['https://spreadsheets.google.com/feeds','https://www.googleapis.com/auth/drive']

	# add credentials to the account
	creds = ServiceAccountCredentials.from_json_keyfile_name('key.json', scope)

	# authorize the clientsheet
	client = gspread.authorize(creds)

	# create the sheet instance (obs.: follow the steps in  https://stackoverflow.com/questions/38949318/google-sheets-api-returns-the-caller-does-not-have-permission-when-using-serve/49965912#49965912)
	sheet = client.open('Registro de Usuários Cluster Apuana  (respostas)')

	worksheet_users = sheet.get_worksheet(0)

	# get current users in the user management spreadsheet
	worksheet_users_vals = worksheet_users.get_all_values()
	worksheet_users_vals = worksheet_users_vals[2:]
	current_users = []

	for row in worksheet_users_vals:
		user = row[1].split('@')
		current_users.append(user[0])

	print('current_users', current_users)

	# get current users in the slurm database
	current_users_slurmdbd = []

	comm = ssh_client.exec_command("sacctmgr -nrp show User")
	channel = comm[1]

	with channel as f:
		try:
			for line in f:
				new_line = line.replace('\n','')
				new_line = new_line.split('|')
				current_users_slurmdbd.append(new_line[0])
		except:
			print("G")

	# verify if there are new users and add them to the slurm database
	print("current_users_slurmdbd", current_users_slurmdbd)
	new_users = list(set(current_users)-set(current_users_slurmdbd))
	print("new_user", new_users)
	if len(new_users) > 0:
		print("new_users = " + str(new_users))
		
		for new_user in new_users:
			print('adding users: ', new_users)

			### previous row to add users ###
			# find user row
			# row_idx = current_users.index(new_user)
			# row = worksheet_users_vals[row_idx]
			# add user to the database
			# print("sacctmgr -i add user " + row[1] + " account=" + row[4] + " partition=" + row[5])

			### add users ###
			ssh_client.exec_command("sacctmgr -i add user " + new_user + " account=test_acc partition=long,short")

		### adjust associations ###
		# os.system("sacctmgr -i modify user set qos=singlegpu where partition=long")
		# os.system("sacctmgr -i modify user set qos=doublegpu where partition=short")
		ssh_client.exec_command("sacctmgr -i modify user set qos=singlegpu where partition=long")
		ssh_client.exec_command("sacctmgr -i modify user set qos=doublegpu where partition=short")

		# os.system("sacctmgr -i modify user set qos=singlegpu where account=test_acc")
		# os.system("sacctmgr -i modify user set qos=doublegpu where account=test_acc")
		ssh_client.exec_command("sacctmgr -i modify user set qos=singlegpu where account=test_acc")
		ssh_client.exec_command("sacctmgr -i modify user set qos=doublegpu where account=test_acc")

		# os.system("sacctmgr -i modify user set qos=normal where partition=test") ## para desenvolvedores
		ssh_client.exec_command("sacctmgr -i modify user set qos=normal where partition=test")

	else:
		print('no new users to add')


def connect_to_slurm():
	while True:
		manager_name = input("Type your manager user: ")
		manager_password = getpass.getpass("Type your manager password: ")

		try:
			ssh_client = paramiko.SSHClient()
			ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
			ssh_client.connect(ip, username=manager_name, password=manager_password)
			print("Connected to slurm manager!!")
			
			return ssh_client
		except paramiko.AuthenticationException:
			print("Authentication failed, please try again")
		except paramiko.SSHException as e:
			print(f"An error occurred: {str(e)}")
		except Exception as e:
			print(f"An error occurred: {str(e)}")
		
		retry = input("Do you want to try again? (y/n): ")
		if retry.lower() != 'y':
			return None


ip = "slurm-manager1.cin.ufpe.br"
ssh_client = connect_to_slurm()

if ssh_client is not None:
	add_users_question = input("Do you want to add new users? (y/n): ")

	if add_users_question.lower() == 'y':
		add_users(ssh_client=ssh_client)
		ssh_client.close()

	else:
		ssh_client.close()

ssh_client.close()
