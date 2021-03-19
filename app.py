from flask import Flask,render_template
import pandas as pd
import requests
import json
import numpy as np
import datetime

app=Flask(__name__)

def return_league_teams(url):
    response=requests.get(url)
    response=json.loads(response.content)
    df=pd.DataFrame(response['standings']['results'])
    return df

def currentgw():
    url = 'https://fantasy.premierleague.com/api/bootstrap-static/'
    response = requests.get(url)
    response = json.loads(response.content)
    for items in response['events']:
        if items['is_current']==True:
            gw=items['id']
    return gw

def cap_and_vice(id):
    each_team='https://fantasy.premierleague.com/api/entry/'+id+'/event/'+str(currentgw())+'/picks/'
    response=requests.get(each_team).content
    response=json.loads(response)
    load_team=response['picks']
    df=pd.DataFrame(load_team)
    cap_id=df[df['is_captain']==True].element.values[0]
    vice_cap_id=df[df['is_vice_captain']==True].element.values[0]
    player_url='https://fantasy.premierleague.com/api/bootstrap-static/'
    player_df=pd.DataFrame((json.loads(requests.get(player_url).content))['elements'])
    cap=player_df[player_df.id==cap_id].second_name.values[0]
    vice_cap=player_df[player_df.id==vice_cap_id].second_name.values[0]
    return cap,vice_cap

def return_cap_vice_per(league_code):
    url='https://fantasy.premierleague.com/api/leagues-classic/'+str(league_code)+'/standings/'
    main_df=return_league_teams(url)
    main_df['captain']=np.nan
    main_df['vice_captain']=np.nan
    for i in range(0,len(main_df)):
        entry=main_df.loc[i,'entry']
        x,y=cap_and_vice(str(entry))
        main_df.loc[i,'captain']=x
        main_df.loc[i,'vice_captain']=y
    first_player_cap=main_df.loc[0,'captain']
    #first_player_vicecap=main_df.loc[0,'vice_captain']
    captain_picks=main_df.captain.values
    vice_captain_picks=main_df.vice_captain.values
    captain_picks=list(captain_picks)
    vice_captain_picks=list(vice_captain_picks)
    total_choosed=captain_picks+vice_captain_picks
    unique_players=list(set(total_choosed))
    player_stats=pd.DataFrame(columns=['name','cap','vice','cap_per','vice_cap_per'])
    
    for name in unique_players:
        i=len(player_stats)
        player_stats.loc[i,'name']=name
        player_stats.loc[i,'cap']=captain_picks.count(name)
        player_stats.loc[i,'vice']=vice_captain_picks.count(name)
    for i in range(0,len(player_stats)):
        player_stats.loc[i,'cap_per']=(int(player_stats.loc[i,'cap'])/len(player_stats))*100
        player_stats.loc[i,'vice_cap_per']=(int(player_stats.loc[i,'vice'])/len(player_stats))*100
    
    
    pop_cap=player_stats[player_stats.cap==player_stats.cap.max()].sample(1).name.values[0]
    vice_pop_cap=player_stats[player_stats.vice==player_stats.vice.max()].sample(1).name.values[0]
    
    pop_cap_per=player_stats[player_stats.name==pop_cap].cap_per.values[0]
    vice_cap_per=player_stats[player_stats.name==vice_pop_cap].vice_cap_per.values[0]
    
    return pop_cap,vice_pop_cap,pop_cap_per,vice_cap_per,first_player_cap

def cap_vice_df(league_code):
    url='https://fantasy.premierleague.com/api/leagues-classic/'+str(league_code)+'/standings/'
    main_df=return_league_teams(url)
    main_df['captain']=np.nan
    main_df['vice_captain']=np.nan
    for i in range(0,len(main_df)):
        entry=main_df.loc[i,'entry']
        x,y=cap_and_vice(str(entry))
        main_df.loc[i,'captain']=x
        main_df.loc[i,'vice_captain']=y
    return main_df

@app.route('/')
def homepage():
    return render_template('home.html',message="Use site followed by /league_code")

@app.route('/<text>')
def home(text):
    df=cap_vice_df(str(text))
    df=df[['entry_name','total','captain','vice_captain']]
    df.columns=['Manager','Total Points','Captain','Vice Captain']

    pop_cap,vice_pop_cap,pop_cap_per,vice_cap_per,first_player_cap=return_cap_vice_per(str(text))
    pop_cap_per=round(float(pop_cap_per),2)
    vice_cap_per=round(float(vice_cap_per),2)
    return render_template("index.html",tables=[df.to_html(classes='data')], titles=df.columns.values,toppercaptain=first_player_cap,pop_cap=pop_cap,pop_cap_per=pop_cap_per,pop_vice_cap=vice_pop_cap,pop_vice_cap_per=vice_cap_per)

#app.run(port=0000)