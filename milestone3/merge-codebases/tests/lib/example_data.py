### contests ###

# For sorting the example contests small -> large,
# which is useful because pytest shrinks toward smaller list indices.
contest_size = lambda c: (len(c['answers']), len(c['question']))

# TODO add referendum examples too

EXAMPLE_CONTESTS = [
  {
    "type": "office",
    "question": "Pirate Captain of the Ship's Company",
    "context": "Golden Age of Piracy — crews elected captains by vote",
    "answers": [
      "Bartholomew Roberts (Black Bart)",
      "Henry Every",
      "Captain Charles Vane",
      "Long John Silver",
      "Anne Bonny"
    ]
  },
  {
    "type": "office",
    "question": "Archon of Athens",
    "context": "Classical Athenian democracy",
    "answers": [
      "Pericles",
      "Cleisthenes",
      "Themistocles",
      "Aristides the Just",
      "Solon"
    ]
  },
  {
    "type": "office",
    "question": "Consul of the Roman Republic",
    "context": "Elected annually by the Centuriate Assembly",
    "answers": [
      "Cicero",
      "Cato the Younger",
      "Gaius Marius",
      "Scipio Africanus",
      "Lucius Junius Brutus"
    ]
  },
  {
    "type": "office",
    "question": "Doge of Venice",
    "context": "Elected by the Venetian aristocracy via an elaborate ballot",
    "answers": [
      "Enrico Dandolo",
      "Francesco Foscari",
      "Sebastiano Venier",
      "Marino Faliero"
    ]
  },
  {
    "type": "office",
    "question": "Pope",
    "context": "Elected by the College of Cardinals",
    "answers": [
      "Cardinal Giovanni de' Medici",
      "Cardinal Roderic Borgia",
      "Cardinal Karol Wojtyła",
      "Cardinal Jorge Bergoglio"
    ]
  },
  {
    "type": "office",
    "question": "Lawspeaker of the Icelandic Althing",
    "context": "Norse Commonwealth's early parliamentary assembly",
    "answers": [
      "Þorgeir Ljósvetningagoði",
      "Grímr Svertingsson",
      "Skapti Þóroddsson",
      "Snorri Sturluson"
    ]
  },
  {
    "type": "office",
    "question": "Mayor of Michel Delving (the Shire)",
    "context": "Tolkien — the Shire elected its Mayor every seven years",
    "answers": [
      "Will Whitfoot",
      "Samwise Gamgee",
      "Frodo Baggins",
      "Meriadoc Brandybuck"
    ]
  },
  {
    "type": "office",
    "question": "President of the United Federation of Planets",
    "context": "Star Trek — democratically elected office",
    "answers": [
      "Jonathan Archer",
      "Nanietta Bacco",
      "Min Zife",
      "Nan Bacco"
    ]
  },
  {
    "type": "office",
    "question": "Jury Foreman",
    "context": "12 Angry Men — jurors elect a foreman",
    "answers": [
      "Juror 1",
      "Juror 8",
      "Juror 3",
      "Juror 4"
    ]
  },
  {
    "type": "office",
    "question": "Trade Union General Secretary",
    "context": "Labour movement — elected by membership ballot",
    "answers": [
      "Walter Reuther",
      "Arthur Scargill",
      "Lech Wałęsa",
      "Mary Harris 'Mother' Jones"
    ]
  },
  {
    "type": "office",
    "question": "Iroquois Confederacy Sachem",
    "context": "Haudenosaunee — sachems chosen by clan mothers/councils",
    "answers": [
      "Hiawatha",
      "Deganawidah (the Great Peacemaker)",
      "Handsome Lake",
      "Cornplanter"
    ]
  },
  {
    "type": "office",
    "question": "Landsgemeinde Councillor",
    "context": "Open-air direct democracy in Appenzell/Glarus (Swiss Canton)",
    "answers": [
      "Ulrich Zwingli",
      "Niklaus von Flüe",
      "Arnold Winkelried",
      "Werner Stauffacher",
      "Heidi's Grandfather (Alm-Öhi)"
    ]
  },
  {
    "type": "office",
    "question": "Tribune of the Plebs",
    "context": "Roman Republic — elected to defend the plebeians",
    "answers": [
      "Tiberius Gracchus",
      "Gaius Gracchus",
      "Publius Clodius Pulcher",
      "Lucius Sicinius",
      "Cola di Rienzo"
    ]
  },
  {
    "type": "office",
    "question": "Grand Master of the Knights Hospitaller",
    "context": "Elected by the order's chapter",
    "answers": [
      "Jean Parisot de Valette",
      "Pierre d'Aubusson",
      "Philippe Villiers de L'Isle-Adam",
      "Fra' Angelo de Mojana"
    ]
  },
  {
    "type": "office",
    "question": "Speaker of the House of Commons",
    "context": "Elected by fellow Members of Parliament",
    "answers": [
    "Thomas More",
      "William Lenthall",
      "Betty Boothroyd",
      "John Bercow"
    ]
  },
  {
    "type": "office",
    "question": "Ecclesia Delegate of the Free City",
    "context": "Guild-and-commune assembly of a medieval free city",
    "answers": [
      "Jacob van Artevelde",
      "Étienne Marcel",
      "Wat Tyler",
      "Cola Pesce"
    ]
  },
  {
    "type": "office",
    "question": "Chief of the Comanche Council",
    "context": "Plains council leadership chosen by consensus/vote of warriors",
    "answers": [
      "Quanah Parker",
      "Buffalo Hump",
      "Ten Bears",
      "Peta Nocona"
    ]
  },
  {
    "type": "office",
    "question": "Rebel Alliance Chief of State",
    "context": "Star Wars — the New Republic Senate elects its leader",
    "answers": [
      "Mon Mothma",
      "Leia Organa",
      "Bail Organa",
      "Ponc Gavrisom"
    ]
  },
  {
    "type": "office",
    "question": "Prime Minister of the Time Lords",
    "context": "Doctor Who — Gallifreyan High Council leadership",
    "answers": [
      "The Doctor",
      "Romana",
      "Rassilon",
      "Chancellor Flavia"
    ]
  },
  {
    "type": "office",
    "question": "Novgorod Veche Posadnik",
    "context": "Medieval Novgorod Republic — mayor elected by the town assembly",
    "answers": [
      "Marfa Boretskaya (Marfa the Mayoress)",
      "Ostromir",
      "Miroshka Nezdinich",
      "Tverdislav Mikhalkovich"
    ]
  },
  {
    "type": "office",
    "question": "President of the Continental Congress",
    "context": "Delegates of the American colonies elected a presiding officer",
    "answers": [
      "John Hancock",
      "Peyton Randolph",
      "Henry Laurens",
      "John Jay"
    ]
  },
  {
    "type": "office",
    "question": "Guildmaster of the Thieves' Guild",
    "context": "Fantasy trope — guild leadership by member vote",
    "answers": [
      "The Gray Mouser",
      "Locke Lamora",
      "Autolycus",
      "Vetinari (pre-Patrician)"
    ]
  },
  {
    "type": "office",
    "question": "Soviet Deputy of the Petrograd Council",
    "context": "1917 — workers' and soldiers' councils elected delegates",
    "answers": [
      "Leon Trotsky",
      "Nikolai Chkheidze",
      "Alexander Kerensky",
      "Matvei Skobelev"
    ]
  },
  {
    "type": "office",
    "question": "Kgotla Chief",
    "context": "Traditional public assembly where the community deliberates (Botswana/Tswana Assembly)",
    "answers": [
      "Khama III",
      "Sechele I",
      "Bathoen I",
      "Seretse Khama"
    ]
  },
  {
    "type": "office",
    "question": "Prom King of Sunnydale High",
    "context": "Teen pop-culture ballot (Buffy-verse)",
    "answers": [
      "Buffy Summers",
      "Cordelia Chase",
      "Xander Harris",
      "Angel"
    ]
  },
  {
    "type": "office",
    "question": "Holy Roman Emperor",
    "context": "The seven Kurfürsten elected the Emperor (Elected by the Prince-Electors)",
    "answers": [
      "Charles V of Habsburg",
      "Frederick the Wise of Saxony",
      "Francis I of France (candidate, 1519)",
      "Henry VII of Luxembourg",
      "Rudolf I of Habsburg"
    ]
  },
  {
    "type": "office",
    "question": "King of Poland",
    "context": "Polish–Lithuanian Commonwealth nobles elected the monarch (Royal Elective Sejm)",
    "answers": [
      "Henry of Valois",
      "Stephen Báthory",
      "Jan III Sobieski",
      "Stanisław August Poniatowski",
      "Augustus II the Strong"
    ]
  },
  {
    "type": "office",
    "question": "Doge of Genoa",
    "context": "Genoese Republic — elected head of state",
    "answers": [
      "Simone Boccanegra",
      "Andrea Doria",
      "Giano I di Campofregoso",
      "Leonardo Montaldo"
    ]
  },
  {
    "type": "office",
    "question": "Gonfaloniere of Justice",
    "context": "Chief magistrate of Florence, chosen by lot/vote of guilds",
    "answers": [
      "Piero Soderini",
      "Niccolò Machiavelli (as Secretary)",
      "Salvestro de' Medici",
      "Michele di Lando"
    ]
  },
  {
    "type": "office",
    "question": "Stadtholder of the Dutch Republic",
    "context": "Provincial States appointed/elected the executive",
    "answers": [
      "William the Silent",
      "Johan de Witt (Grand Pensionary)",
      "Maurice of Nassau",
      "William III of Orange"
    ]
  },
  {
    "type": "office",
    "question": "Great Khan",
    "context": "Mongol chiefs assembled to elect the Khan (Mongol Kurultai)",
    "answers": [
    "Genghis Khan (Temüjin)",
      "Ögedei Khan",
      "Möngke Khan",
      "Kublai Khan",
      "Güyük Khan"
    ]
  },
  {
    "type": "office",
    "question": "Rashidun Caliph",
    "context": "Early Islamic succession by council of companions (Shura Council)",
    "answers": [
      "Abu Bakr",
      "Umar ibn al-Khattab",
      "Uthman ibn Affan",
      "Ali ibn Abi Talib"
    ]
  },
  {
    "type": "office",
    "question": "President of the Roman Senate",
    "context": "Senior senator recognized by censors' selection (Princeps Senatus)",
    "answers": [
      "Fabius Maximus",
      "Appius Claudius Caecus",
      "Marcus Aemilius Scaurus",
      "Quintus Fabius Maximus Rullianus"
    ]
  },
  {
    "type": "office",
    "question": "Ephor of Sparta",
    "context": "Five overseers elected annually by the Spartan assembly",
    "answers": [
      "Chilon of Sparta",
      "Sthenelaidas",
      "Antalcidas",
      "Epitadeus"
    ]
  },
  {
    "type": "office",
    "question": "Landamman of the Swiss Confederation",
    "context": "Cantonal chief magistrate chosen by assembly",
    "answers": [
      "Werner Stauffacher",
      "Hans Waldmann",
      "Nikolaus Leuenberger",
      "Aloys Reding"
    ]
  },
  {
    "type": "office",
    "question": "Doge-equivalent: Capitano del Popolo",
    "context": "Elected communal official of Siena (Sienese Republic)",
    "answers": [
      "Provenzano Salvani",
      "Pandolfo Petrucci",
      "Ambrogio Lorenzetti (as councillor)",
      "Buonconte da Montefeltro"
    ]
  },
  {
    "type": "office",
    "question": "Speaker of the Frankish Thing / Placitum",
    "context": "Germanic freemen's assembly settling law and leadership",
    "answers": [
      "Clovis I",
      "Arbogast",
      "Chlothar II",
      "Pepin of Herstal"
    ]
  },
  {
    "type": "office",
    "question": "Chairman of the Zaporozhian Cossack Rada",
    "context": "Cossacks elected their Hetman by open assembly vote",
    "answers": [
      "Bohdan Khmelnytsky",
      "Petro Konashevych-Sahaidachny",
      "Ivan Mazepa",
      "Ivan Sirko"
    ]
  },
  {
    "type": "office",
    "question": "Consul of the Carthaginian Suffetes",
    "context": "Carthage elected two suffetes annually",
    "answers": [
      "Hanno the Great",
      "Hamilcar Barca",
      "Mago the Elder",
      "Bomilcar"
    ]
  },
  {
    "type": "office",
    "question": "President of the Twelve Colonies",
    "context": "Battlestar Galactica New series — democratic elections held aboard the fleet",
    "answers": [
      "Laura Roslin",
      "Gaius Baltar",
      "Tom Zarek",
      "Wallace Gray"
    ]
  },
  {
    "type": "office",
    "question": "President of the Panem District Council",
    "context": "The Hunger Games — post-war democratic reforms",
    "answers": [
      "Alma Coin",
      "Plutarch Heavensbee",
      "Paylor",
      "Katniss Everdeen"
    ]
  },
  {
    "type": "office",
    "question": "Leader of the Mutant Council of Krakoa",
    "context": "Marvel comics — the Quiet Council governed Krakoa",
    "answers": [
      "Professor Charles Xavier",
      "Magneto",
      "Emma Frost",
      "Storm"
    ]
  },
  {
    "type": "office",
    "question": "President of the United States",
    "context": "Fictional US presidential elections (The West Wing)",
    "answers": [
      "Josiah 'Jed' Bartlet",
      "Matt Santos",
      "Arnold Vinick",
      "Robert Ritchie"
    ]
  },
  {
    "type": "office",
    "question": "Justice League Chairperson",
    "context": "DC comics — the League votes on membership and leadership",
    "answers": [
      "Superman",
      "Wonder Woman",
      "Batman",
      "Martian Manhunter"
    ]
  },
  {
    "type": "office",
    "question": "President of the Galactic Senate",
    "context": "Star Wars prequels — the Supreme Chancellor is elected",
    "answers": [
      "Finis Valorum",
      "Sheev Palpatine",
      "Padmé Amidala (nominated)",
      "Bail Organa"
    ]
  },
  {
    "type": "office",
    "question": "Mayor of Pawnee, Indiana",
    "context": "Parks and Recreation — local elected office",
    "answers": [
      "Leslie Knope",
      "Bobby Newport",
      "Paul Iaresco",
      "Ron Swanson"
    ]
  },
  {
    "type": "office",
    "question": "President of the United States",
    "context": "Satirical US political campaigns and elections (Veep)",
    "answers": [
      "Selina Meyer",
      "Jonah Ryan",
      "Bill O'Brien",
      "Tom James"
    ]
  },
  {
    "type": "office",
    "question": "Chief of the Avengers Council",
    "context": "Marvel — team leadership decided by the roster",
    "answers": [
      "Captain America (Steve Rogers)",
      "Iron Man (Tony Stark)",
      "Captain Marvel (Carol Danvers)",
      "Black Panther (T'Challa)"
    ]
  },
  {
    "type": "office",
    "question": "President of the New Republic",
    "context": "Star Wars — reconstituted democratic senate (The Mandalorian era)",
    "answers": [
      "Mon Mothma",
      "Leia Organa",
      "Tai Kolma",
      "Ransolm Casterfo"
    ]
  },
  {
    "type": "office",
    "question": "Head Girl / Head Boy of Malory Towers",
    "context": "Enid Blyton — school leadership chosen by pupils/staff",
    "answers": [
      "Darrell Rivers",
      "Sally Hope",
      "Alicia Johns",
      "Gwendoline Mary Lacey"
    ]
  },
  {
    "type": "office",
    "question": "President of the Galactic Federation",
    "context": "Animated sci-fi — democratic space government (Futurama)",
    "answers": [
      "Richard Nixon's Head",
      "John Jackson",
      "Jack Johnson",
      "Chris Travers"
    ]
  },
  {
    "type": "office",
    "question": "Prime Minister",
    "context": "British political satire — Westminster leadership (Yes, Minister / The Thick of It)",
    "answers": [
      "Jim Hacker",
      "Tom Sargent",
      "Nicola Murray",
      "Peter Mannion"
    ]
  },
  {
    "type": "office",
    "question": "President of the United States",
    "context": "American Revolution",
    "answers": [
      "George Washington", "Thomas Jefferson", "John Adams",
      "Benjamin Franklin", "Alexander Hamilton", "James Madison",
      "John Jay", "Samuel Adams", "Patrick Henry", "John Hancock"
    ]
  },
  {
    "type": "office",
    "question": "Captain of the Hispaniola",
    "context": "Treasure Island by Robert Louis Stevenson",
    "answers": [
      "Long John Silver", "Billy Bones", "Captain Flint",
      "Israel Hands", "Ben Gunn", "Captain Smollett",
      "Blind Pew", "Jim Hawkins"
    ]
  },
  {
    "type": "office",
    "question": "Mayor of Gotham City",
    "context": "Batman (DC Comics)",
    "answers": [
      "Bruce Wayne", "Harvey Dent", "James Gordon",
      "Oswald Cobblepot", "Selina Kyle", "Lucius Fox"
    ]
  },
  {
    "type": "office",
    "question": "Chief of the Lakota",
    "context": "Lakota Sioux leaders",
    "answers": [
      "Sitting Bull", "Crazy Horse", "Red Cloud",
      "Spotted Tail", "Rain-in-the-Face"
    ]
  }

]

EXAMPLE_CONTESTS.sort(key=contest_size)
