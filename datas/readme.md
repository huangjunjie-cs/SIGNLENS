## Data Download

You can download dataset in [kaggle dataset](https://www.kaggle.com/h12345jack/signlens/download)


## Data Description
The tsv data is divided by \t, and the data includes 3 parts

We show the instruction for ```cbdb_edgelist.tsv```

1. Edgelist

| PersonIdA |	PersonIdB|	Sign |	Time | 	Note |
| ------ | ----- | ------- | ----- | ---- |
| 449689 |	13575 |	1 |	-1 |	438 |

2. EdgeInfo

| Note | Info |
| ----- | ---- |
| 438 | 	{"Info": "\u6536\u5230Y\u7684\u8d08\u8a69\u3001\u6587", "Sign": 1} |

The info is ```JSON``` file like

```
{
"Info":"收到Y的贈詩、文" ,
"Sign":1
}
```
It means that "Received poems and essays from Y" fro 438

3. NodeInfo

| PersonId | Info |
| ----- | ---- |
| 135757 |	{"PersonId": "135757", "EngName": "Chen Gai", "ChName": "\u9673\u69e9", "IndexYear": "1155", "Gender": "0", "YearBirth": "1096", "DynastyBirth": "\u5317\u5b8b", "EraBirth": "\u7d39\u8056", "EraYearBirth": "3", "YearDeath": "", "DynastyDeath": "\u672a\u8a73", "EraDeath": "\u672a\u8a73", "EraYearDeath": "", "YearsLived": "", "Dynasty": "\u5b8b", "JunWang": "\u3010\u672a\u8a73\u3011", "Notes": "Index year algorithmically generated: Rule 3;", "url": "https://cbdb.fas.harvard.edu/cbdbapi/person.php?id=135757&o=json"} |

The info is ```JSON``` file like

```
{
"PersonId":"135757",
"EngName":"Chen Gai",
"ChName":"陳槩",
"IndexYear":"1155",
"Gender":"0",
"YearBirth":"1096",
"DynastyBirth":"北宋",
"EraBirth":"紹聖",
"EraYearBirth":"3",
"YearDeath":"",
"DynastyDeath":"未詳",
"EraDeath":"未詳",
"EraYearDeath":"",
"YearsLived":"",
"Dynasty":"宋",
"JunWang":"【未詳】",
"Notes":"Index year algorithmically generated: Rule 3;",
"url":"https://cbdb.fas.harvard.edu/cbdbapi/person.php?id=135757&o=json"
}
```

