#!/usr/bin/env node

const fs = require("fs");
const path = require("path");

const repoRoot = path.resolve(__dirname, "..");
const configPath = path.join(repoRoot, "skills.config.json");

function main() {
  const command = process.argv[2] || "list";

  try {
    switch (command) {
      case "list":
        runList();
        break;
      case "validate":
        runValidate();
        break;
      case "pack":
        runPack();
        break;
      default:
        printHelp();
        process.exitCode = 1;
    }
  } catch (error) {
    console.error(`Error: ${error.message}`);
    process.exitCode = 1;
  }
}

function loadConfig() {
  return JSON.parse(fs.readFileSync(configPath, "utf8"));
}

function discoverSkills() {
  const config = loadConfig();
  const skillsRoot = path.join(repoRoot, config.skillsDirectory);

  if (!fs.existsSync(skillsRoot)) {
    throw new Error(`skills directory not found: ${skillsRoot}`);
  }

  const entries = fs
    .readdirSync(skillsRoot, { withFileTypes: true })
    .filter((entry) => entry.isDirectory())
    .map((entry) => readSkill(path.join(skillsRoot, entry.name), entry.name));

  return { config, skillsRoot, skills: entries };
}

function readSkill(skillDir, dirName) {
  const skillPath = path.join(skillDir, "SKILL.md");
  const result = {
    dirName,
    skillDir,
    skillPath,
    exists: fs.existsSync(skillPath),
    name: "",
    description: "",
  };

  if (!result.exists) {
    return result;
  }

  const content = fs.readFileSync(skillPath, "utf8");
  const trimmed = content.trim();

  if (!trimmed) {
    return result;
  }

  const frontmatter = parseFrontmatter(content);
  result.name = (frontmatter.name || "").trim();
  result.description = normalizeDescription(frontmatter.description || "");
  return result;
}

function parseFrontmatter(content) {
  const match = content.match(/^---\n([\s\S]*?)\n---/);
  if (!match) {
    return {};
  }

  const lines = match[1].split("\n");
  const data = {};
  let activeKey = null;

  for (const line of lines) {
    if (!line.trim()) {
      continue;
    }

    const mapped = line.match(/^([A-Za-z0-9_-]+):\s*(.*)$/);
    if (mapped) {
      const [, key, value] = mapped;
      activeKey = key;

      if (value === "|") {
        data[key] = "";
      } else {
        data[key] = value.trim();
      }
      continue;
    }

    if (activeKey && line.startsWith("  ")) {
      const nextLine = line.trim();
      data[activeKey] = data[activeKey]
        ? `${data[activeKey]}\n${nextLine}`
        : nextLine;
    }
  }

  return data;
}

function normalizeDescription(value) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean)
    .join(" ");
}

function validateSkills(skills) {
  const errors = [];
  const names = new Map();

  for (const skill of skills) {
    if (!skill.exists) {
      errors.push(`${skill.dirName}: missing SKILL.md`);
      continue;
    }

    const content = fs.readFileSync(skill.skillPath, "utf8").trim();
    if (!content) {
      errors.push(`${skill.dirName}: SKILL.md is empty`);
      continue;
    }

    if (!skill.name) {
      errors.push(`${skill.dirName}: missing frontmatter name`);
    }

    if (!skill.description) {
      errors.push(`${skill.dirName}: missing frontmatter description`);
    }

    if (skill.name && skill.name !== skill.dirName) {
      errors.push(
        `${skill.dirName}: frontmatter name must match directory name (${skill.name})`
      );
    }

    if (skill.name) {
      if (names.has(skill.name)) {
        errors.push(`${skill.dirName}: duplicate skill name ${skill.name}`);
      } else {
        names.set(skill.name, skill.dirName);
      }
    }
  }

  return errors;
}

function runList() {
  const { skills } = discoverSkills();
  const validSkills = skills.filter((skill) => skill.exists && skill.name);

  for (const skill of validSkills) {
    console.log(`${skill.name}\t${skill.description}`);
  }
}

function runValidate() {
  const { config, skills } = discoverSkills();
  const errors = validateSkills(skills);

  if (errors.length > 0) {
    console.error("Validation failed:");
    for (const error of errors) {
      console.error(`- ${error}`);
    }
    process.exit(1);
  }

  console.log(
    `Validated ${skills.length} skills in ${path.relative(repoRoot, path.join(repoRoot, config.skillsDirectory))}`
  );
}

function runPack() {
  const { config, skills } = discoverSkills();
  const errors = validateSkills(skills);

  if (errors.length > 0) {
    console.error("Validation failed:");
    for (const error of errors) {
      console.error(`- ${error}`);
    }
    process.exit(1);
  }

  const distDir = path.join(repoRoot, "dist");
  fs.mkdirSync(distDir, { recursive: true });

  const manifestPath = path.join(repoRoot, config.mpmPublish.manifestPath);
  fs.mkdirSync(path.dirname(manifestPath), { recursive: true });

  const manifest = {
    repoName: config.repoName,
    displayName: config.displayName,
    publicRepository: config.publicRepository,
    archiveFormat: config.archiveFormat,
    generatedAt: new Date().toISOString(),
    skills: skills.map((skill) => ({
      name: skill.name,
      directory: path.relative(repoRoot, skill.skillDir),
      skillPath: path.relative(repoRoot, skill.skillPath),
      description: skill.description,
    })),
  };

  fs.writeFileSync(manifestPath, `${JSON.stringify(manifest, null, 2)}\n`, "utf8");
  console.log(`Wrote ${path.relative(repoRoot, manifestPath)}`);
}

function printHelp() {
  console.log("Usage: node ./bin/my-skills.js <list|validate|pack>");
}

main();
