### contests ###

# For sorting the example contests small -> large,
# which is useful because pytest shrinks toward smaller list indices.
contest_size = lambda c: (len(c['candidates']), len(c['office']))

EXAMPLE_CONTESTS = [
  {
    "office": "Pirate Captain of the Ship's Company",
    "context": "Golden Age of Piracy — crews elected captains by vote",
    "candidates": [
      "Bartholomew Roberts (Black Bart)",
      "Henry Every",
      "Captain Charles Vane",
      "Long John Silver",
      "Anne Bonny"
    ]
  },
  {
    "office": "Archon of Athens",
    "context": "Classical Athenian democracy",
    "candidates": [
      "Pericles",
      "Cleisthenes",
      "Themistocles",
      "Aristides the Just",
      "Solon"
    ]
  },
  {
    "office": "Consul of the Roman Republic",
    "context": "Elected annually by the Centuriate Assembly",
    "candidates": [
      "Cicero",
      "Cato the Younger",
      "Gaius Marius",
      "Scipio Africanus",
      "Lucius Junius Brutus"
    ]
  },
  {
    "office": "Doge of Venice",
    "context": "Elected by the Venetian aristocracy via an elaborate ballot",
    "candidates": [
      "Enrico Dandolo",
      "Francesco Foscari",
      "Sebastiano Venier",
      "Marino Faliero"
    ]
  },
  {
    "office": "Pope",
    "context": "Elected by the College of Cardinals",
    "candidates": [
      "Cardinal Giovanni de' Medici",
      "Cardinal Roderic Borgia",
      "Cardinal Karol Wojtyła",
      "Cardinal Jorge Bergoglio"
    ]
  },
  {
    "office": "Lawspeaker of the Icelandic Althing",
    "context": "Norse Commonwealth's early parliamentary assembly",
    "candidates": [
      "Þorgeir Ljósvetningagoði",
      "Grímr Svertingsson",
      "Skapti Þóroddsson",
      "Snorri Sturluson"
    ]
  },
  {
    "office": "Mayor of Michel Delving (the Shire)",
    "context": "Tolkien — the Shire elected its Mayor every seven years",
    "candidates": [
      "Will Whitfoot",
      "Samwise Gamgee",
      "Frodo Baggins",
      "Meriadoc Brandybuck"
    ]
  },
  {
    "office": "President of the United Federation of Planets",
    "context": "Star Trek — democratically elected office",
    "candidates": [
      "Jonathan Archer",
      "Nanietta Bacco",
      "Min Zife",
      "Nan Bacco"
    ]
  },
  {
    "office": "Jury Foreman",
    "context": "12 Angry Men — jurors elect a foreman",
    "candidates": [
      "Juror 1",
      "Juror 8",
      "Juror 3",
      "Juror 4"
    ]
  },
  {
    "office": "Trade Union General Secretary",
    "context": "Labour movement — elected by membership ballot",
    "candidates": [
      "Walter Reuther",
      "Arthur Scargill",
      "Lech Wałęsa",
      "Mary Harris 'Mother' Jones"
    ]
  },
  {
    "office": "Iroquois Confederacy Sachem",
    "context": "Haudenosaunee — sachems chosen by clan mothers/councils",
    "candidates": [
      "Hiawatha",
      "Deganawidah (the Great Peacemaker)",
      "Handsome Lake",
      "Cornplanter"
    ]
  },
  {
    "office": "Landsgemeinde Councillor",
    "context": "Open-air direct democracy in Appenzell/Glarus (Swiss Canton)",
    "candidates": [
      "Ulrich Zwingli",
      "Niklaus von Flüe",
      "Arnold Winkelried",
      "Werner Stauffacher",
      "Heidi's Grandfather (Alm-Öhi)"
    ]
  },
  {
    "office": "Tribune of the Plebs",
    "context": "Roman Republic — elected to defend the plebeians",
    "candidates": [
      "Tiberius Gracchus",
      "Gaius Gracchus",
      "Publius Clodius Pulcher",
      "Lucius Sicinius",
      "Cola di Rienzo"
    ]
  },
  {
    "office": "Grand Master of the Knights Hospitaller",
    "context": "Elected by the order's chapter",
    "candidates": [
      "Jean Parisot de Valette",
      "Pierre d'Aubusson",
      "Philippe Villiers de L'Isle-Adam",
      "Fra' Angelo de Mojana"
    ]
  },
  {
    "office": "Speaker of the House of Commons",
    "context": "Elected by fellow Members of Parliament",
    "candidates": [
    "Thomas More",
      "William Lenthall",
      "Betty Boothroyd",
      "John Bercow"
    ]
  },
  {
    "office": "Ecclesia Delegate of the Free City",
    "context": "Guild-and-commune assembly of a medieval free city",
    "candidates": [
      "Jacob van Artevelde",
      "Étienne Marcel",
      "Wat Tyler",
      "Cola Pesce"
    ]
  },
  {
    "office": "Chief of the Comanche Council",
    "context": "Plains council leadership chosen by consensus/vote of warriors",
    "candidates": [
      "Quanah Parker",
      "Buffalo Hump",
      "Ten Bears",
      "Peta Nocona"
    ]
  },
  {
    "office": "Rebel Alliance Chief of State",
    "context": "Star Wars — the New Republic Senate elects its leader",
    "candidates": [
      "Mon Mothma",
      "Leia Organa",
      "Bail Organa",
      "Ponc Gavrisom"
    ]
  },
  {
    "office": "Prime Minister of the Time Lords",
    "context": "Doctor Who — Gallifreyan High Council leadership",
    "candidates": [
      "The Doctor",
      "Romana",
      "Rassilon",
      "Chancellor Flavia"
    ]
  },
  {
    "office": "Novgorod Veche Posadnik",
    "context": "Medieval Novgorod Republic — mayor elected by the town assembly",
    "candidates": [
      "Marfa Boretskaya (Marfa the Mayoress)",
      "Ostromir",
      "Miroshka Nezdinich",
      "Tverdislav Mikhalkovich"
    ]
  },
  {
    "office": "President of the Continental Congress",
    "context": "Delegates of the American colonies elected a presiding officer",
    "candidates": [
      "John Hancock",
      "Peyton Randolph",
      "Henry Laurens",
      "John Jay"
    ]
  },
  {
    "office": "Guildmaster of the Thieves' Guild",
    "context": "Fantasy trope — guild leadership by member vote",
    "candidates": [
      "The Gray Mouser",
      "Locke Lamora",
      "Autolycus",
      "Vetinari (pre-Patrician)"
    ]
  },
  {
    "office": "Soviet Deputy of the Petrograd Council",
    "context": "1917 — workers' and soldiers' councils elected delegates",
    "candidates": [
      "Leon Trotsky",
      "Nikolai Chkheidze",
      "Alexander Kerensky",
      "Matvei Skobelev"
    ]
  },
  {
    "office": "Kgotla Chief",
    "context": "Traditional public assembly where the community deliberates (Botswana/Tswana Assembly)",
    "candidates": [
      "Khama III",
      "Sechele I",
      "Bathoen I",
      "Seretse Khama"
    ]
  },
  {
    "office": "Prom King of Sunnydale High",
    "context": "Teen pop-culture ballot (Buffy-verse)",
    "candidates": [
      "Buffy Summers",
      "Cordelia Chase",
      "Xander Harris",
      "Angel"
    ]
  },
  {
    "office": "Holy Roman Emperor",
    "context": "The seven Kurfürsten elected the Emperor (Elected by the Prince-Electors)",
    "candidates": [
      "Charles V of Habsburg",
      "Frederick the Wise of Saxony",
      "Francis I of France (candidate, 1519)",
      "Henry VII of Luxembourg",
      "Rudolf I of Habsburg"
    ]
  },
  {
    "office": "King of Poland",
    "context": "Polish–Lithuanian Commonwealth nobles elected the monarch (Royal Elective Sejm)",
    "candidates": [
      "Henry of Valois",
      "Stephen Báthory",
      "Jan III Sobieski",
      "Stanisław August Poniatowski",
      "Augustus II the Strong"
    ]
  },
  {
    "office": "Doge of Genoa",
    "context": "Genoese Republic — elected head of state",
    "candidates": [
      "Simone Boccanegra",
      "Andrea Doria",
      "Giano I di Campofregoso",
      "Leonardo Montaldo"
    ]
  },
  {
    "office": "Gonfaloniere of Justice",
    "context": "Chief magistrate of Florence, chosen by lot/vote of guilds",
    "candidates": [
      "Piero Soderini",
      "Niccolò Machiavelli (as Secretary)",
      "Salvestro de' Medici",
      "Michele di Lando"
    ]
  },
  {
    "office": "Stadtholder of the Dutch Republic",
    "context": "Provincial States appointed/elected the executive",
    "candidates": [
      "William the Silent",
      "Johan de Witt (Grand Pensionary)",
      "Maurice of Nassau",
      "William III of Orange"
    ]
  },
  {
    "office": "Great Khan",
    "context": "Mongol chiefs assembled to elect the Khan (Mongol Kurultai)",
    "candidates": [
    "Genghis Khan (Temüjin)",
      "Ögedei Khan",
      "Möngke Khan",
      "Kublai Khan",
      "Güyük Khan"
    ]
  },
  {
    "office": "Rashidun Caliph",
    "context": "Early Islamic succession by council of companions (Shura Council)",
    "candidates": [
      "Abu Bakr",
      "Umar ibn al-Khattab",
      "Uthman ibn Affan",
      "Ali ibn Abi Talib"
    ]
  },
  {
    "office": "President of the Roman Senate",
    "context": "Senior senator recognized by censors' selection (Princeps Senatus)",
    "candidates": [
      "Fabius Maximus",
      "Appius Claudius Caecus",
      "Marcus Aemilius Scaurus",
      "Quintus Fabius Maximus Rullianus"
    ]
  },
  {
    "office": "Ephor of Sparta",
    "context": "Five overseers elected annually by the Spartan assembly",
    "candidates": [
      "Chilon of Sparta",
      "Sthenelaidas",
      "Antalcidas",
      "Epitadeus"
    ]
  },
  {
    "office": "Landamman of the Swiss Confederation",
    "context": "Cantonal chief magistrate chosen by assembly",
    "candidates": [
      "Werner Stauffacher",
      "Hans Waldmann",
      "Nikolaus Leuenberger",
      "Aloys Reding"
    ]
  },
  {
    "office": "Doge-equivalent: Capitano del Popolo",
    "context": "Elected communal official of Siena (Sienese Republic)",
    "candidates": [
      "Provenzano Salvani",
      "Pandolfo Petrucci",
      "Ambrogio Lorenzetti (as councillor)",
      "Buonconte da Montefeltro"
    ]
  },
  {
    "office": "Speaker of the Frankish Thing / Placitum",
    "context": "Germanic freemen's assembly settling law and leadership",
    "candidates": [
      "Clovis I",
      "Arbogast",
      "Chlothar II",
      "Pepin of Herstal"
    ]
  },
  {
    "office": "Chairman of the Zaporozhian Cossack Rada",
    "context": "Cossacks elected their Hetman by open assembly vote",
    "candidates": [
      "Bohdan Khmelnytsky",
      "Petro Konashevych-Sahaidachny",
      "Ivan Mazepa",
      "Ivan Sirko"
    ]
  },
  {
    "office": "Consul of the Carthaginian Suffetes",
    "context": "Carthage elected two suffetes annually",
    "candidates": [
      "Hanno the Great",
      "Hamilcar Barca",
      "Mago the Elder",
      "Bomilcar"
    ]
  },
  {
    "office": "President of the Twelve Colonies",
    "context": "Battlestar Galactica New series — democratic elections held aboard the fleet",
    "candidates": [
      "Laura Roslin",
      "Gaius Baltar",
      "Tom Zarek",
      "Wallace Gray"
    ]
  },
  {
    "office": "President of the Panem District Council",
    "context": "The Hunger Games — post-war democratic reforms",
    "candidates": [
      "Alma Coin",
      "Plutarch Heavensbee",
      "Paylor",
      "Katniss Everdeen"
    ]
  },
  {
    "office": "Leader of the Mutant Council of Krakoa",
    "context": "Marvel comics — the Quiet Council governed Krakoa",
    "candidates": [
      "Professor Charles Xavier",
      "Magneto",
      "Emma Frost",
      "Storm"
    ]
  },
  {
    "office": "President of the United States",
    "context": "Fictional US presidential elections (The West Wing)",
    "candidates": [
      "Josiah 'Jed' Bartlet",
      "Matt Santos",
      "Arnold Vinick",
      "Robert Ritchie"
    ]
  },
  {
    "office": "Justice League Chairperson",
    "context": "DC comics — the League votes on membership and leadership",
    "candidates": [
      "Superman",
      "Wonder Woman",
      "Batman",
      "Martian Manhunter"
    ]
  },
  {
    "office": "President of the Galactic Senate",
    "context": "Star Wars prequels — the Supreme Chancellor is elected",
    "candidates": [
      "Finis Valorum",
      "Sheev Palpatine",
      "Padmé Amidala (nominated)",
      "Bail Organa"
    ]
  },
  {
    "office": "Mayor of Pawnee, Indiana",
    "context": "Parks and Recreation — local elected office",
    "candidates": [
      "Leslie Knope",
      "Bobby Newport",
      "Paul Iaresco",
      "Ron Swanson"
    ]
  },
  {
    "office": "President of the United States",
    "context": "Satirical US political campaigns and elections (Veep)",
    "candidates": [
      "Selina Meyer",
      "Jonah Ryan",
      "Bill O'Brien",
      "Tom James"
    ]
  },
  {
    "office": "Chief of the Avengers Council",
    "context": "Marvel — team leadership decided by the roster",
    "candidates": [
      "Captain America (Steve Rogers)",
      "Iron Man (Tony Stark)",
      "Captain Marvel (Carol Danvers)",
      "Black Panther (T'Challa)"
    ]
  },
  {
    "office": "President of the New Republic",
    "context": "Star Wars — reconstituted democratic senate (The Mandalorian era)",
    "candidates": [
      "Mon Mothma",
      "Leia Organa",
      "Tai Kolma",
      "Ransolm Casterfo"
    ]
  },
  {
    "office": "Head Girl / Head Boy of Malory Towers",
    "context": "Enid Blyton — school leadership chosen by pupils/staff",
    "candidates": [
      "Darrell Rivers",
      "Sally Hope",
      "Alicia Johns",
      "Gwendoline Mary Lacey"
    ]
  },
  {
    "office": "President of the Galactic Federation",
    "context": "Animated sci-fi — democratic space government (Futurama)",
    "candidates": [
      "Richard Nixon's Head",
      "John Jackson",
      "Jack Johnson",
      "Chris Travers"
    ]
  },
  {
    "office": "Prime Minister",
    "context": "British political satire — Westminster leadership (Yes, Minister / The Thick of It)",
    "candidates": [
      "Jim Hacker",
      "Tom Sargent",
      "Nicola Murray",
      "Peter Mannion"
    ]
  },
  {
    "office": "President of the United States",
    "context": "American Revolution",
    "candidates": [
      "George Washington", "Thomas Jefferson", "John Adams",
      "Benjamin Franklin", "Alexander Hamilton", "James Madison",
      "John Jay", "Samuel Adams", "Patrick Henry", "John Hancock"
    ]
  },
  {
    "office": "Captain of the Hispaniola",
    "context": "Treasure Island by Robert Louis Stevenson",
    "candidates": [
      "Long John Silver", "Billy Bones", "Captain Flint",
      "Israel Hands", "Ben Gunn", "Captain Smollett",
      "Blind Pew", "Jim Hawkins"
    ]
  },
  {
    "office": "Mayor of Gotham City",
    "context": "Batman (DC Comics)",
    "candidates": [
      "Bruce Wayne", "Harvey Dent", "James Gordon",
      "Oswald Cobblepot", "Selina Kyle", "Lucius Fox"
    ]
  },
  {
    "office": "Chief of the Lakota",
    "context": "Lakota Sioux leaders",
    "candidates": [
      "Sitting Bull", "Crazy Horse", "Red Cloud",
      "Spotted Tail", "Rain-in-the-Face"
    ]
  }

]

EXAMPLE_CONTESTS.sort(key=contest_size)
