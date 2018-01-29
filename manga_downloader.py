import requests, os, urllib
from bs4 import BeautifulSoup
from tqdm import tqdm
from pathlib import Path
from PIL import Image
from io import BytesIO


def get_manga_link(manga_site, manga_directory, manga_name) :
	manga_link = ''

	if manga_site == "MangaStream":
		base_url = 'https://readms.net'
		# First we request all the link tags
		page_content = manga_directory.find('div', {'class' : 'col-sm-8'})
		link_tags = page_content.find_all('a')
		# Then we search in every tag for the name of the manga
		list_of_mangas = [] 
		for every_link_tag in link_tags :
	  		if manga_name.lower() in every_link_tag.text.lower() :
	  			list_of_mangas.append(every_link_tag)
	  	
	  	print "\n[*] List of available mangas [*]\n"
	  	manga_number = 0
	  	for every_manga in list_of_mangas:
	  		print '[' + str(manga_number) + '] - ' + every_manga.text
	  		manga_number += 1

	  	while True:	
	  		try:
	  			chosen_manga = int(raw_input())
	  			manga_link = base_url + list_of_mangas[chosen_manga].get('href')
	  			manga_name = list_of_mangas[chosen_manga].text
	  			break
	  		except IndexError:
	  			print "\nError\n"

	forbiden_dir_chars_windows = ['/', '\\', ':', '*', '?', '"', '<', '>' ,'|']
	for every_forbiden_char in forbiden_dir_chars_windows:
		if every_forbiden_char in manga_name:
			manga_name = manga_name.replace(every_forbiden_char, ' ')

	return manga_link, manga_name


def list_of_available_chapters(manga_site, manga_link, manga_name) :
	list_of_chapters = []

	if manga_site == "MangaStream":
		base_url = 'https://readms.net'
		page = BeautifulSoup(requests.get(manga_link).text,'html.parser')
		print '\n[*] Chapters List - ' + manga_name + ' [*]\n'
		
		chapter_table = page.find('table', {'class' : 'table table-striped'})
		list_of_elements = chapter_table.find_all('td')

		list_of_chapters = []

		for every_element in list_of_elements :
			if every_element.find('a'):
				chapter_name = every_element.text
				# Create a tuple of (chapter name, chapter number, chapter link)
				if ':' in chapter_name:
					chapter_name.replace(':', ' - ')
				list_of_chapters.append((chapter_name, chapter_name.split(' ')[0].lstrip('0').encode('utf-8'), base_url + every_element.find('a').get('href').encode('utf-8')))
			else:
				released_date = every_element.text
				print chapter_name + '  (' + released_date + ')'

	return list_of_chapters


def download_chapters(chapter_link, chapter_dir, base_url, chapter_name):
	
	# Request the page of the chapter
	page = BeautifulSoup(requests.get(chapter_link).text,'html.parser')

	# Getting the number of pages in the chapter
	last_page = page.find_all('ul', {'class' : 'dropdown-menu'})[4].find_all('a')
	for every_element in last_page:
		if "Last" in every_element.text:
			# We search for the word 'last' because mangastreat uses it in the site
			number_of_pages = int(every_element.get('href').split('/')[-1])

	list_of_links = []

	for page_number in range(1,number_of_pages):
		# Getting the page that contains the image and the next page/image
		page_ = page.find('div', {'class' : 'page'})
		# Building a generic link for the chapters
		img_link = 'https:' + page_.find('img').get('src').encode('utf-8')
		next_page = base_url + page_.find('a').get('href').encode('utf-8')
		list_of_links.append(img_link)
		page = BeautifulSoup(requests.get(next_page).text,'html.parser')

	
	print "[*] Downloading - " + chapter_name + " [*]"
	
	with tqdm(total= (number_of_pages - 1)) as pbar:
		for every_link in list_of_links :

			path_to_save_the_image = chapter_dir + '/' + every_link.split('/')[-1]

			check_if_file_exist = Path(path_to_save_the_image)

			if not check_if_file_exist.is_file():
				img_content = requests.get(every_link).content
				open(path_to_save_the_image, 'wb').write(img_content)

			pbar.update(1)

		pbar.close() 
    		

def chapters_manager(manga_site, list_of_chapters, manga_name):

	print "\n\n[1] Download all available chapters."
	print "[2] Download latest chapter."
	print "[3] Specify chapters to download (Chapter number sperated by comma)."
	action = int(raw_input('\nChoose an option : \n')) 

	try: 
		os.makedirs(manga_name)
	except OSError:
		pass

	if manga_site == 'MangaStream':
		base_url = 'https://readms.net'

		# Action 1 - Downloading all chapters
		if action == 1:
			for every_chapter in list_of_chapters:
				# every_chapter is a tuple (chapter name[0], chapter number[1], chapter link[2])
				chapter_dir = manga_name + '/' + every_chapter[0]
				try: 
					os.makedirs(chapter_dir)
				except OSError:
					pass
				# Download the chapter
				download_chapters(every_chapter[2], chapter_dir, base_url, every_chapter[0])

		# Action 2 - Downloading the latest chapter
		elif action == 2:
			latest_chapter = list_of_chapters[0]
			chapter_dir = manga_name + '/' + latest_chapter[0]
			try: 
				os.makedirs(chapter_dir)
			except OSError:
				pass
			# Download the chapter
			download_chapters(latest_chapter[2], chapter_dir, base_url, latest_chapter[0])

		# Action 3 - Downlading specific chapters
		elif action == 3:
			list_of_specific_chapters = []
			user_input_of_chapters = str(raw_input())
			tmp_list_of_specific_chapters = user_input_of_chapters.split(',')
			for every_chapter_number in tmp_list_of_specific_chapters:
				list_of_specific_chapters.append(every_chapter_number.strip())

			for every_chapter in list_of_chapters:
				if every_chapter[1] in list_of_specific_chapters:
					chapter_dir = manga_name + '/' + every_chapter[0]
					try: 
						os.makedirs(chapter_dir)
					except OSError:
						pass

					# Download the chapter
					download_chapters(every_chapter[2], chapter_dir, base_url, every_chapter[0])

if __name__ == '__main__':

	manga_site = int(raw_input('Choose your manga website : \n[1] - MangaStream\n'))
	if manga_site == 1:
		manga_name = str(raw_input('Enter the name of the manga you want to download :\n'))
		manga_directory = BeautifulSoup(requests.get('https://readms.net/manga').text,'html.parser')
		manga_link, manga_name = get_manga_link('MangaStream', manga_directory, manga_name)
		if manga_link != '':
			list_of_chapters = list_of_available_chapters("MangaStream", manga_link, manga_name)
			chapters_manager('MangaStream', list_of_chapters, manga_name)
		else:
			print '\nThere Are No Mangas Available With This Name'

