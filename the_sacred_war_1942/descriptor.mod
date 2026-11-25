version="2.0.0"
tags={
	"Alternative History"
	"Events"
	"Map"
	"Military"
	"Technologies"
	"Ideologies"
	"Graphics"
}
name="The Sacred War - 1942"
picture="thumbnail.png"
supported_version="1.20.*"
remote_file_id="3142844611"

# --- Notes on load order (game 1.17+ doctrine system) --------------------
#
# NO replace_path is used anywhere in this mod, on purpose.
#
# * common/technologies/artillery.txt and common/technologies/industry.txt
#   override vanilla because they have the SAME FILE NAME as the vanilla
#   files. That is how the mod has always worked; replace_path is not needed
#   for it.
#
# * We deliberately do NOT replace_path any common/doctrines folder. In 1.17+
#   the naval, air and special-forces doctrines live in those same folders as
#   grand doctrines. Replacing the folder would delete them, leaving vanilla's
#   naval/air grand doctrines pointing at tracks that no longer exist.
#
# * The mod's four land grand doctrines therefore use distinct ids prefixed
#   sw_ (sw_mobile_warfare, sw_superior_firepower, sw_grand_battleplan,
#   sw_mass_assault) so they cannot collide with vanilla's four land grand
#   doctrines (mobile_warfare, superior_firepower, grand_battleplan,
#   mass_assault). Both sets are selectable; see readme_ai.md for how to hide
#   the vanilla four if that is ever wanted.
#
# * The old technology-based doctrine tree is NO LONGER in
#   common/technologies/. It was moved to design_record/ so the game does not
#   parse it, because 1.17+ removed land doctrine technologies and the 64 old
#   tech ids would otherwise be re-added to the technology tree.
