import json
import os
import requests
import datetime


months = {}
months["1"] = "January"
months["2"] = "February"
months["3"] = "March"
months["4"] = "April"
months["5"] = "May"
months["6"] = "June"
months["7"] = "July"
months["8"] = "August"
months["9"] = "September"
months["10"] = "October"
months["11"] = "November"
months["12"] = "December"

def read_json(filepath):
    inp = {}
    with open(filepath) as json_data:
        inp = json.load(json_data)
    if(type(inp) == tuple):
        data_type = inp[1]
    else:
        data_type = type(inp)
    return inp, data_type
def save_json(data, filepath):
    try:
        r = json.dumps(data)
        loaded_r = json.loads(r)
        with open(filepath, 'w') as outfile:
            json.dump(loaded_r, outfile, indent=4)
        return True
    except Exception as e:
        print(e)
        return False
def save_profile_pic(path, name, url):
  with open(path + name + ".png", 'wb') as handle:
    response = requests.get(url, stream=True)
    if not response.ok:
      print(response)
    for block in response.iter_content(1024):
      if not block:
        break
      handle.write(block)
def get_sessionize_json(url):
  response = requests.get(url)
  if not response.ok:
    print(response)
  body = response.json()
  return body

people_image_path = "../images/people/"
sessionize_speakers_url = "https://sessionize.com/api/v2/lo4pjfv9/view/Speakers"
sessionize_speakers_wall_url  = "https://sessionize.com/api/v2/lo4pjfv9/view/SpeakerWall"
sessions_url  = "https://sessionize.com/api/v2/lo4pjfv9/view/Sessions"
schedule_table_url  = "https://sessionize.com/api/v2/lo4pjfv9/view/GridTable"
schedule_smart_grid_url  = "https://sessionize.com/api/v2/lo4pjfv9/view/GridSmart"

speakers = get_sessionize_json(sessionize_speakers_url)
save_json(speakers, "speakers.json")
speakers_wall = get_sessionize_json(sessionize_speakers_wall_url)
save_json(speakers_wall, "speakers_wall.json")
sessions = get_sessionize_json(sessions_url)
save_json(sessions, "sessions.json")
schedule_table = get_sessionize_json(schedule_table_url)
save_json(schedule_table, "schedule_table.json")
schedule_smartgrid = get_sessionize_json(schedule_smart_grid_url)
save_json(schedule_smartgrid, "schedule_smartgrid.json")
data, cls = read_json("../docs/default-firebase-data.json")
save_json(data, "../docs/default-firebase-data-bkp.json")
print(data.keys())

schedule_details, cls = read_json("schedule_table.json")
sessions_details, cls = read_json("sessions.json")
speakers, cls = read_json("speakers.json")
speaker_wall, cls = read_json("speakers_wall.json")

def get_date_time(dtime):
  ymd = dtime.split("T")
  tt = ymd[1]
  ymd = ymd[0]
  ymd1 = ymd.split("-")
  ymd1 = months[ymd1[1]] + " " + ymd1[2] + " " + ymd1[0]
  return ymd, ymd1, tt

##################################################################### Sessions ###########################################################################
def session_builder(sessions_details):
    all_session_info = {}
    session_slots = {}
    tracks = {}
    for ses in sessions_details:
      sess_det = ses['sessions']
      for det in sess_det:
        new_ses = {}
        id = det["id"]
        session_slots[id] = {"startTime": det['startsAt'], "endTime": det['endsAt']}
        new_ses["description"] = det["description"]
        new_ses["title"] = det["title"]

        new_ses["speakers"] = []
        for speak in det["speakers"]:
          new_ses["speakers"].append(speak['name'])
        new_ses["icon"] = ''
        new_ses["videoID"] = ''
        new_ses["image"] = ''
        new_ses["presentation"] = ''
        new_ses["roomId"] = det["roomId"]
        new_ses["room"] = det["room"]

        for cat in det["categories"]:
          if cat["name"].lower() == "language":
            language = ""
            for lan in cat['categoryItems']:
              language += lan["name"] + ","
            language = list(language)[0:len(language)-1]
            new_ses["language"] = "".join(language)

          if cat["name"].lower() == "level":
            level = ""
            for lev in cat['categoryItems']:
              level += lev["name"] + ","
            level = list(level)[0:len(level) - 1]
            new_ses["complexity"] = "".join(level)

          if cat["name"].lower() == "track":
            track = ""
            for trk in cat['categoryItems']:
              track += trk["name"] + ","
            track = list(track)[0:len(track) - 1]
            new_ses["tags"] = "".join(track)
            new_ses["track"] = "".join(track)
            dat0, dat1, dat2 =  get_date_time(det['startsAt'])
            if dat0 not in tracks.keys():
              tracks[dat0] = {}
            if new_ses["track"] not in tracks[dat0].keys():
              tracks[dat0][new_ses["track"]] = {}
            if det["roomId"] not in tracks[dat0][new_ses["track"]].keys():
              tracks[dat0][new_ses["track"]][det["roomId"]] = det["room"]
          if cat["name"].lower() == "session format":
            track = ""
            for trk in cat['categoryItems']:
              track += trk["name"] + ","
            track = list(track)[0:len(track) - 1]
            new_ses["session_format"] = "".join(track)
        all_session_info[id] = new_ses
    return all_session_info, session_slots, tracks

session_det, session_slots, session_tracks  =  session_builder(sessions_details)
data["sessions"] = session_builder(sessions_details)


##################################################################### Schedule ###########################################################################
print("schedule")
sch_ref = data["schedule"]['2019-11-22']
print(sch_ref.keys())
print("schedule details")

schedule = {}
timeslots = {}
for slotid, det in session_slots.items():
  date, read, tt = get_date_time(det["startTime"])
  if date not in timeslots.keys():
    timeslots[date] = {}
  tm = tt.split(":")
  tm = tm[0] + "." + tm[1]
  if tm not in timeslots[date]:
    timeslots[date][tm] = {}
  date, read, tt = get_date_time(det["endTime"])
  tm1 = tt.split(":")
  tm1 = tm1[0] + "." + tm1[1]
  if tm1 not in timeslots[date][tm]:
    timeslots[date][tm][tm1] = []
  timeslots[date][tm][tm1].append(slotid)

for sc in schedule_details:
  date, read, tt = get_date_time(sc["date"])
  schedule[date]= {}
  schedule[date]['dateReadable'] = read

  for s_rm in sc["rooms"]:
    for s_tm in s_rm["sessions"]:
        d_st_tm, r_st_tm, tt_st_tm = get_date_time(s_tm['startsAt'])
        d_ed_tm, r_ed_tm, tt_ed_tm = get_date_time(s_tm['endsAt'])
        tm = tt_st_tm.split(":")
        tm = tm[0] + "." + tm[1]
        if tm not in timeslots[date]:
          timeslots[date][tm] = {}
        tm1 = tt_ed_tm.split(":")
        tm1 = tm1[0] + "." + tm1[1]
        if tm1 not in timeslots[date][tm]:
          timeslots[date][tm][tm1] = []
        timeslots[date][tm][tm1].append(s_tm["id"])
  schedule[date]['timeslots'] = []
  schedule[date]['tracks'] = []

for date in schedule.keys():
  slots_tms = timeslots[date]
  tmslots = []
  for st in slots_tms.keys():
    for et, ids in slots_tms[st].items():
      tmp = {}
      tmp["startTime"] = st
      tmp["endTime"] = et
      tmp["sessions"] = []
      for id in ids:
        item = {'items': [id]}
        tmp["sessions"].append(item)
      tmslots.append(tmp)
  schedule[date]['timeslots'] = tmslots
  sessinf = session_tracks[date]
  sesstrack = []
  for track, roo_det in sessinf.items():
    tmp = {}
    tmp["title"] = track
    tmp["roomId"] = []
    tmp["room_name"] = []
    for roomid, nm in roo_det.items():
      tmp["roomId"].append(roomid)
      tmp["room_name"].append(nm)
    sesstrack.append(tmp)
  schedule[date]["tracks"] = sesstrack

data["schedule"] = schedule


##################################################################### SPEAKERS ###########################################################################

def insert_speaker(speakers, speaker_wall):
  speakers_reference = {}
  order = 1
  for speaker in speakers:
    for sw in speaker_wall:
      if sw["id"] == speaker["id"]:
        speaker["tagLine"] = sw["tagLine"]
        speaker["isTopSpeaker"] = sw['isTopSpeaker']

    name_key = speaker["firstName"] + "_" + speaker["lastName"]
    reference_speaker_info = {}
    reference_speaker_info["name"] = speaker["fullName"]
    reference_speaker_info["bio"] = speaker["bio"]
    reference_speaker_info["shortBio"] = speaker['tagLine']
    reference_speaker_info["title"] = speaker['tagLine']
    reference_speaker_info["order"] = str(order)
    order = order + 1
    picUrl = speaker['profilePicture']
    picname = speaker["firstName"].lower() + "." + speaker["lastName"].lower()
    save_profile_pic(people_image_path,picname,picUrl)
    reference_speaker_info["photo"] = '/images/people/' + picname + '.png'
    reference_speaker_info["photoUrl"] = 'https://www.devfestyyc.com/images/people/' + picname + '.png'
    reference_speaker_info['featured'] = speaker['isTopSpeaker']
    reference_speaker_info['socials']=[]

    if len(speaker['links'])>0:
      for ln in speaker['links']:
        if ln['title'].lower() == "linkedin":
          ref_social = {'icon': 'linkedin', 'link': '', 'name': 'LinkedIn'}
          ref_social['link'] = ln['url']
        elif ln['title'].lower() == "twitter":
          ref_social = {'icon': 'twitter', 'link': '', 'name': 'Twitter'}
          ref_social['link'] = ln['url']
        elif ln['title'].lower() == "github":
          ref_social = {'icon': 'github', 'link': '', 'name': 'Github'}
          ref_social['link'] = ln['url']
        else:
          ref_social = {}
        reference_speaker_info['socials'].append(ref_social)
    qa = speaker["questionAnswers"]
    if len(qa) > 0:
      for q in qa:
        if q['question'] == '1. Current Organization/ Company Name':
          if str(q['answer']).lower() != "none":
            reference_speaker_info['company'] = q['answer']
          else:
            reference_speaker_info['company'] = ''
    speakers_reference[name_key] = reference_speaker_info
  return speakers_reference

data["speakers"] = insert_speaker(speakers, speaker_wall)

################################################################################# SAVE NEW FILE ###########################################################################################3
save_json(data, "../docs/default-firebase-data.json")