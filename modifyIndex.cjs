const fs = require("fs");
const readline = require("readline");

async function modifyMainIndex(indexFilePath) {
	const linkRegexPattern = /\[\[(?!.+?:)([^\]\[]+)\|([^\]\[]+)\]\]/i;
	const filterList = ["read-and-watch-list"];

	const fileStream = fs.createReadStream(indexFilePath);
	let modifiedFile = "";

	const rl = readline.createInterface({
		input: fileStream,
		crlfDelay: Infinity,
	});

	for await (const line of rl) {
		let patternSearch = line.match(linkRegexPattern);
		if (patternSearch) {
			if (!filterList.includes(patternSearch[1])) {
				modifiedFile += `${line}\n`;
			}
		} else {
			modifiedFile += `${line}\n`;
		}
	}

	fs.writeFile(indexFilePath, modifiedFile, (err) => {
		if (err) {
			console.error(err);
		}
	});
}

modifyMainIndex(process.argv[2]);
