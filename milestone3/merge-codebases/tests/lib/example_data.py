# For making the example contests usable in hypothesis.
# def freeze(obj):
#     if isinstance(obj, dict):
#         return tuple(sorted((k, freeze(v)) for k, v in obj.items()))
#     if isinstance(obj, list):
#         return tuple(freeze(x) for x in obj)
#     return obj

# For sorting the example contests small -> large,
# which is useful because pytest shrinks toward smaller list indices.
contest_size = lambda c: (len(c['candidates']), len(c['office']))

EXAMPLE_CONTESTS = [
    {
        "office": "President of the United States",
        "note": "American Revolution",
        "candidates": [
            "George Washington", "Thomas Jefferson", "John Adams",
            "Benjamin Franklin", "Alexander Hamilton", "James Madison",
            "John Jay", "Samuel Adams", "Patrick Henry", "John Hancock"
        ]
    },
    {
        "office": "King of Denmark",
        "note": "Hamlet by William Shakespeare",
        "candidates": [
            "Hamlet", "Claudius", "Polonius", "Laertes",
            "Horatio", "Fortinbras", "Rosencrantz", "Guildenstern"
        ]
    },
    {
        "office": "Captain of the Hispaniola",
        "note": "Treasure Island by Robert Louis Stevenson",
        "candidates": [
            "Long John Silver", "Billy Bones", "Captain Flint",
            "Israel Hands", "Ben Gunn", "Captain Smollett",
            "Blind Pew", "Jim Hawkins"
        ]
    },
    {
        "office": "King of Camelot",
        "note": "Arthurian legend / Knights of the Round Table",
        "candidates": [
            "King Arthur", "Lancelot", "Sir Gawain", "Sir Galahad",
            "Merlin", "Percival", "Mordred", "Sir Kay",
            "Sir Bedivere", "Sir Tristan", "Sir Gareth"
        ]
    },
    {
        "office": "Ruler of Middle-earth",
        "note": "The Lord of the Rings by J.R.R. Tolkien",
        "candidates": [
            "Aragorn", "Gandalf", "Frodo Baggins", "Samwise Gamgee",
            "Legolas", "Gimli", "Boromir", "Galadriel",
            "Elrond", "Theoden", "Faramir", "Denethor"
        ]
    },
    {
        "office": "Roman Emperor",
        "note": "Late Roman Republic / Empire",
        "candidates": [
            "Julius Caesar", "Augustus", "Mark Antony", "Brutus",
            "Cassius", "Pompey", "Nero", "Caligula",
            "Marcus Aurelius", "Cicero", "Crassus"
        ]
    },
    {
        "office": "Headmaster of Hogwarts",
        "note": "Harry Potter by J.K. Rowling",
        "candidates": [
            "Albus Dumbledore", "Minerva McGonagall", "Severus Snape",
            "Rubeus Hagrid", "Horace Slughorn", "Filius Flitwick",
            "Pomona Sprout", "Dolores Umbridge"
        ]
    },
    {
        "office": "Queen of Egypt",
        "note": "Ancient Egyptian queens",
        "candidates": [
            "Cleopatra", "Nefertiti", "Hatshepsut", "Nefertari",
            "Ankhesenamun"
        ]
    },
    {
        "office": "King of the Jungle",
        "note": "The Lion King (Disney)",
        "candidates": [
            "Simba", "Mufasa", "Scar", "Rafiki",
            "Zazu", "Nala", "Timon", "Pumbaa"
        ]
    },
    {
        "office": "Mayor of Gotham City",
        "note": "Batman (DC Comics)",
        "candidates": [
            "Bruce Wayne", "Harvey Dent", "James Gordon",
            "Oswald Cobblepot", "Selina Kyle", "Lucius Fox"
        ]
    },
    {
        "office": "Ruler of Narnia",
        "note": "The Chronicles of Narnia by C.S. Lewis",
        "candidates": [
            "Aslan", "Peter Pevensie", "Susan Pevensie",
            "Edmund Pevensie", "Lucy Pevensie", "Caspian",
            "Mr. Tumnus", "The White Witch", "Reepicheep"
        ]
    },
    {
        "office": "Ruler of Olympus",
        "note": "Greek mythology",
        "candidates": [
            "Zeus", "Poseidon", "Hades", "Athena",
            "Apollo", "Ares", "Hermes", "Hephaestus",
            "Aphrodite", "Artemis", "Demeter", "Hera"
        ]
    },
    {
        "office": "Captain of the Starship Enterprise",
        "note": "Star Trek (The Original Series)",
        "candidates": [
            "James T. Kirk", "Spock", "Leonard McCoy",
            "Montgomery Scott", "Hikaru Sulu", "Nyota Uhura",
            "Pavel Chekov"
        ]
    },
    {
        "office": "Sheriff of Nottingham",
        "note": "Robin Hood legend",
        "candidates": [
            "Robin Hood", "Little John", "Friar Tuck",
            "Will Scarlet", "Maid Marian", "Much the Miller's Son",
            "Alan-a-Dale", "Guy of Gisbourne", "Prince John"
        ]
    },
    {
        "office": "President of the Galactic Republic",
        "note": "Star Wars",
        "candidates": [
            "Luke Skywalker", "Leia Organa", "Han Solo",
            "Obi-Wan Kenobi", "Yoda", "Mace Windu",
            "Padmé Amidala", "Lando Calrissian", "Chewbacca"
        ]
    },
    {
        "office": "Emperor of China",
        "note": "Romance of the Three Kingdoms",
        "candidates": [
            "Liu Bei", "Cao Cao", "Sun Quan", "Zhuge Liang",
            "Guan Yu", "Zhang Fei", "Lü Bu", "Zhao Yun"
        ]
    },
    {
        "office": "Godfather of the Corleone Family",
        "note": "The Godfather by Mario Puzo / Francis Ford Coppola films",
        "candidates": [
            "Vito Corleone", "Michael Corleone", "Sonny Corleone",
            "Fredo Corleone", "Tom Hagen", "Peter Clemenza"
        ]
    },
    {
        "office": "Lord of Winterfell",
        "note": "A Song of Ice and Fire / Game of Thrones by George R.R. Martin",
        "candidates": [
            "Eddard Stark", "Robb Stark", "Jon Snow",
            "Sansa Stark", "Arya Stark", "Bran Stark",
            "Theon Greyjoy", "Catelyn Stark"
        ]
    },
    {
        "office": "Prime Minister of Toad Hall",
        "note": "The Wind in the Willows by Kenneth Grahame",
        "candidates": [
            "Mr. Toad", "Ratty (Water Rat)", "Mole",
            "Badger", "Otter"
        ]
    },
    {
        "office": "Wizard of Oz",
        "note": "The Wonderful Wizard of Oz by L. Frank Baum",
        "candidates": [
            "Dorothy Gale", "Scarecrow", "Tin Man",
            "Cowardly Lion", "The Wizard", "Glinda the Good Witch",
            "Wicked Witch of the West", "Toto"
        ]
    },
    {
        "office": "Leader of the Justice League",
        "note": "Justice League (DC Comics)",
        "candidates": [
            "Superman", "Batman", "Wonder Woman", "The Flash",
            "Aquaman", "Green Lantern", "Cyborg", "Martian Manhunter"
        ]
    },
    {
        "office": "Leader of the Avengers",
        "note": "The Avengers (Marvel Comics / MCU)",
        "candidates": [
            "Iron Man", "Captain America", "Thor", "Hulk",
            "Black Widow", "Hawkeye", "Black Panther",
            "Doctor Strange", "Spider-Man", "Captain Marvel"
        ]
    },
    {
        "office": "Detective of Scotland Yard",
        "note": "Sherlock Holmes by Arthur Conan Doyle",
        "candidates": [
            "Sherlock Holmes", "Dr. John Watson", "Inspector Lestrade",
            "Mycroft Holmes", "Irene Adler", "Mrs. Hudson",
            "Professor Moriarty"
        ]
    },
    {
        "office": "Norse All-Father",
        "note": "Norse mythology",
        "candidates": [
            "Odin", "Thor", "Loki", "Freya",
            "Baldr", "Heimdall", "Tyr", "Frigg", "Njord"
        ]
    },
    {
        "office": "King of France",
        "note": "The Three Musketeers by Alexandre Dumas",
        "candidates": [
            "d'Artagnan", "Athos", "Porthos", "Aramis",
            "Cardinal Richelieu", "Milady de Winter", "King Louis XIII"
        ]
    },
    {
        "office": "Queen of Hearts",
        "note": "Alice's Adventures in Wonderland by Lewis Carroll",
        "candidates": [
            "Alice", "The Mad Hatter", "The White Rabbit",
            "The Cheshire Cat", "The Queen of Hearts", "The King of Hearts",
            "The March Hare", "The Caterpillar", "The Dormouse"
        ]
    },
    {
        "office": "Leader of the Exodus",
        "note": "Book of Exodus (Hebrew Bible)",
        "candidates": [
            "Moses", "Aaron", "Miriam", "Ramesses",
            "Joshua", "Zipporah"
        ]
    },
    {
        "office": "Emperor of Rome",
        "note": "I, Claudius by Robert Graves / Julio-Claudian dynasty",
        "candidates": [
            "Claudius", "Augustus", "Tiberius", "Caligula",
            "Livia", "Germanicus", "Agrippina"
        ]
    },
    {
        "office": "Leader of the French Revolution",
        "note": "French Revolution",
        "candidates": [
            "Maximilien Robespierre", "Georges Danton",
            "Jean-Paul Marat", "Napoleon Bonaparte",
            "Lafayette", "Camille Desmoulins"
        ]
    },
    {
        "office": "Captain of the Pequod",
        "note": "Moby-Dick by Herman Melville",
        "candidates": [
            "Captain Ahab", "Ishmael", "Queequeg",
            "Starbuck", "Stubb", "Flask"
        ]
    },
    {
        "office": "President of Panem",
        "note": "The Hunger Games by Suzanne Collins",
        "candidates": [
            "Katniss Everdeen", "Peeta Mellark", "Haymitch Abernathy",
            "President Snow", "Gale Hawthorne", "Effie Trinket",
            "Cinna", "Finnick Odair"
        ]
    },
    {
        "office": "Tsar of Russia",
        "note": "Russian history",
        "candidates": [
            "Ivan the Terrible", "Peter the Great", "Catherine the Great",
            "Nicholas II", "Rasputin", "Boris Godunov",
            "Alexander Nevsky", "Anastasia"
        ]
    },
    {
        "office": "Emperor of the Mongols",
        "note": "Mongol Empire",
        "candidates": [
            "Genghis Khan", "Kublai Khan", "Ogedei Khan",
            "Marco Polo", "Subutai", "Jochi"
        ]
    },
    {
        "office": "Shogun of Japan",
        "note": "Sengoku (Warring States) period Japan",
        "candidates": [
            "Oda Nobunaga", "Toyotomi Hideyoshi", "Tokugawa Ieyasu",
            "Takeda Shingen", "Uesugi Kenshin", "Date Masamune",
            "Miyamoto Musashi"
        ]
    },
    {
        "office": "Leader of the Pilgrimage to the West",
        "note": "Journey to the West (classic Chinese novel)",
        "candidates": [
            "Sun Wukong (Monkey King)", "Tang Sanzang (Tripitaka)",
            "Zhu Bajie (Pigsy)", "Sha Wujing (Sandy)",
            "the Dragon Horse"
        ]
    },
    {
        "office": "Chief of the Lakota",
        "note": "Lakota Sioux leaders",
        "candidates": [
            "Sitting Bull", "Crazy Horse", "Red Cloud",
            "Spotted Tail", "Rain-in-the-Face"
        ]
    },
    {
        "office": "Emperor of the Aztecs",
        "note": "Aztec Empire",
        "candidates": [
            "Montezuma II", "Cuauhtemoc", "Itzcoatl",
            "Ahuitzotl", "Cuitlahuac"
        ]
    },
    {
        "office": "Sapa Inca",
        "note": "Inca Empire",
        "candidates": [
            "Pachacuti", "Atahualpa", "Huayna Capac",
            "Huascar", "Manco Inca", "Tupac Amaru"
        ]
    },
    {
        "office": "Liberator of South America",
        "note": "South American wars of independence",
        "candidates": [
            "Simon Bolivar", "Jose de San Martin", "Bernardo O'Higgins",
            "Antonio Jose de Sucre", "Francisco de Miranda"
        ]
    },
    {
        "office": "Pharaoh of Egypt",
        "note": "New Kingdom of Ancient Egypt",
        "candidates": [
            "Tutankhamun", "Ramesses II", "Akhenaten",
            "Hatshepsut", "Thutmose III", "Seti I"
        ]
    },
    {
        "office": "King of Persia",
        "note": "Achaemenid Persian Empire",
        "candidates": [
            "Cyrus the Great", "Darius the Great", "Xerxes",
            "Cambyses", "Artaxerxes"
        ]
    },
    {
        "office": "King of the Zulu Kingdom",
        "note": "Zulu Kingdom",
        "candidates": [
            "Shaka Zulu", "Dingane", "Cetshwayo",
            "Nandi", "Mpande"
        ]
    },
    {
        "office": "Emperor of Mali",
        "note": "Mali Empire",
        "candidates": [
            "Mansa Musa", "Sundiata Keita", "Sakura",
            "Mansa Sulayman"
        ]
    },
    {
        "office": "Trickster Chief",
        "note": "West African / Akan folklore (Anansi tales)",
        "candidates": [
            "Anansi the Spider", "the Tortoise", "the Hare",
            "the Lion", "the Elephant"
        ]
    },
    {
        "office": "Ruler of Babylon",
        "note": "Epic of Gilgamesh",
        "candidates": [
            "Hammurabi", "Nebuchadnezzar II", "Gilgamesh",
            "Enkidu", "Sargon of Akkad"
        ]
    }
]

EXAMPLE_CONTESTS.sort(key=contest_size)
# EXAMPLE_CONTESTS = tuple(EXAMPLE_CONTESTS)
