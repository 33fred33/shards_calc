import streamlit as st
import random

# Define the Skin class
db_colors = ["red", "blue", "pink", "grey"]
db_pieces = ["road", "settlement", "city"]

class Drop:
    def __init__(self, skin_index, color_index, piece_index, percentage):
        self.skin_index = skin_index
        self.color = color_index
        self.piece = db_pieces[piece_index]
        self.percentage = percentage

    def __str__(self):
        return f"Drop Skin{self.skin_index}: {self.color} {self.piece} ({self.percentage}%)"
    
    def __eq__(self, other):
        return (self.skin_index == other.skin_index and
                self.color == other.color and
                self.piece == other.piece)

class Skin:
    def __init__(self, index, colors=4, pieces_per_color=3, percentage_per_piece=4.0):
        self.index = index
        self.colors = colors
        self.pieces_per_color = pieces_per_color
        self.percentage_per_piece = percentage_per_piece
    
    @property
    def pieces(self):
        return self.colors * self.pieces_per_color
    
    @property
    def total_percentage(self):
        return self.pieces * self.percentage_per_piece

    def __str__(self):
        return f"Skin {self.index}"# (Colors: {self.colors}, Pieces/Color: {self.pieces_per_color})"

class Chest:
    def __init__(self, skins, days_available, shards_cost, key_shards_cost):
        self.shards_cost = shards_cost
        self.key_shards_cost = key_shards_cost
        self.skins = skins
        self.days_available = days_available
        self.outcome_dict = {}
        cumulative_probability = 0.0
        for skin in skins:
            for iColor in range(skin.colors):
                for iPiece in range(skin.pieces_per_color):
                    drop = Drop(skin_index=skin.index, color_index=iColor, piece_index=iPiece, percentage=cumulative_probability/100.0)
                    cumulative_probability += skin.percentage_per_piece
                    self.outcome_dict[cumulative_probability/100.0] = drop
        self.potential_drops = [drop for drop in self.outcome_dict.values()]
        self.n_potential_drops = len(self.potential_drops)

    def total_pieces(self):
        return sum(skin.pieces for skin in self.skins)

    def total_percentage(self):
        return sum(skin.total_percentage for skin in self.skins)
    
    def simulate_open(self):
        random_number = random.random()
        for probability, drop in self.outcome_dict.items():
            if random_number <= probability:
                return drop
        return None
    
    def shards_needed(self, n_chests):
        """
        Calculate the cost in shards for a given number of chests.
        """
        return n_chests * (self.shards_cost + self.key_shards_cost)

class ChestOpeningSprint:
    def __init__(self, chest):
        self.chest = chest
        self.total_chests = 0
        self.total_unique_drops = []
        #variables to record results

    def run(self, max_chests=100000):
        """
        Simulate opening a chest until all the sets in it are complete.
        """
        # Simulate opening chests until all sets are complete. Returns True if all sets are complete, False otherwise. Also returns the number of chests needed to complete each first, second, etc color and skin.
        chests_per_color_set = {} #the first full color needed x chests, the second needed x chests, etc.
        chests_per_skin = {} #the first full skin needed x chests, the second needed x chests, etc.
        sets_complete = False
        n_colors_complete = 0
        n_sets_complete = 0
        pieces_count = {(skin.index, iColor): 0 for skin in self.chest.skins for iColor in range(skin.colors)}

        while self.total_chests < max_chests and not sets_complete:
            drop = self.chest.simulate_open()
            self.total_chests += 1
            if drop is None:
                continue
            if drop not in self.total_unique_drops:
                #Add drop
                pieces_count[(drop.skin_index, drop.color)] += 1
                self.total_unique_drops.append(drop)

                #Check if a new color was completed
                temp_n_colors_complete = 0
                temp_n_sets_complete = 0
                color_sets_per_skin = {skin.index: 0 for skin in self.chest.skins}
                skin_map = {skin.index: skin for skin in self.chest.skins}
                for key, count in pieces_count.items():
                    skin_index, color_index = key
                    if count == skin_map[skin_index].pieces_per_color:
                        color_sets_per_skin[skin_index] += 1
                        temp_n_colors_complete += 1
                #Check if a new skin was completed
                for skin_index, color_count in color_sets_per_skin.items():
                    if color_count == skin_map[skin_index].colors:
                        temp_n_sets_complete += 1
                #Update the number of colors and skins completed
                if temp_n_colors_complete > n_colors_complete:
                    n_colors_complete = temp_n_colors_complete
                    chests_per_color_set[n_colors_complete] = self.total_chests
                if temp_n_sets_complete > n_sets_complete:
                    n_sets_complete = temp_n_sets_complete
                    chests_per_skin[n_sets_complete] = self.total_chests
                #Check if all skins are complete
                if n_sets_complete == len(self.chest.skins):
                    sets_complete = True
                    return True, chests_per_color_set, chests_per_skin
                
        return False, chests_per_color_set, chests_per_skin
    
def run_for_average(chest, n_runs=1000):
    """
    Run the simulation for a number of runs and return the average number of chests needed to complete all sets.
    """
    cumulative_total_chests = [None for _ in range(n_runs)]
    cumulative_chests_per_color_set = [None for _ in range(n_runs)]
    cumulative_chests_per_skin = [None for _ in range(n_runs)]
    for i in range(n_runs):
        chestOpeningSprint = ChestOpeningSprint(chest)
        _, chests_per_color_set, chests_per_skin = chestOpeningSprint.run()
        cumulative_total_chests[i] = chestOpeningSprint.total_chests
        cumulative_chests_per_color_set[i] = chests_per_color_set
        cumulative_chests_per_skin[i] = chests_per_skin
    total_chests_avg = sum(cumulative_total_chests) / n_runs
    max_colors_completed = max(cumulative_chests_per_color_set, key=lambda x: len(x))
    max_skins_completed = max(cumulative_chests_per_skin, key=lambda x: len(x))
    
    chests_per_color_set_avg = [None for _ in range(len(max_colors_completed))]
    for idx, color_key in enumerate(sorted(max_colors_completed.keys())):
        cumulative_cumulative_chests = 0
        for j in range(n_runs):
            if color_key in cumulative_chests_per_color_set[j]:
                cumulative_cumulative_chests += cumulative_chests_per_color_set[j][color_key]
        chests_per_color_set_avg[idx] = cumulative_cumulative_chests / n_runs

    chests_per_skin_avg = [0.0 for _ in range(len(max_skins_completed))]
    for idx, skin_key in enumerate(sorted(max_skins_completed.keys())):
        total = 0
        count = 0
        for j in range(n_runs):
            if skin_key in cumulative_chests_per_skin[j]:
                total += cumulative_chests_per_skin[j][skin_key]
                count += 1
        chests_per_skin_avg[idx] = total / count if count > 0 else 0.0
        
    return total_chests_avg, chests_per_color_set_avg, chests_per_skin_avg
    
def display_percentage(precedent_text, percentage):
    if percentage > 100:
        st.markdown(f"<span style='color:red'>{precedent_text}: {percentage:.2f}%</span>", unsafe_allow_html=True)
    else:
        st.write(f"{precedent_text}: {percentage:.2f}%")


def estimate_chests_to_any_set(p: float,
                              m: int,
                              k: int,
                              trials: int = 20000) -> float:
    """
    Monte Carlo estimate of the number of chests needed to complete ANY one of k sets.
    
    Parameters
    ----------
    p : float
        Per-chest drop probability of *each* individual piece.
    m : int
        Number of distinct pieces in a set (e.g. 3 for {road, settlement, city}).
    k : int
        Number of different sets available in the chest.
    trials : int, optional
        Number of simulated players to average over (default: 200_000).
        
    Returns
    -------
    float
        Estimated average number of chests to open to complete any one full set.
    """
    # Precompute total drop chance per chest, and flatten the list of pieces
    # We'll label the pieces 0,1,...,k*m-1, where pieces i*m:(i+1)*m belong to set i.
    total_piece_prob = p * m * k
    
    total_chests = 0
    for _ in range(trials):
        counts = [0]*k     # counts[i] = how many pieces of set i we have so far
        chests = 0
        # Keep opening until one set reaches m
        while True:
            chests += 1
            r = random.random()
            if r < total_piece_prob:
                # we got *some* piece: find which one
                # each piece has equal weight p, so we can integer-divide by p to pick an index:
                piece_index = int(r // p)
                set_index   = piece_index // m
                counts[set_index] += 1
                if counts[set_index] == m:
                    break
            # else: r >= total_piece_prob → "no useful piece" this chest
        total_chests += chests
    
    return total_chests / trials


# Initialize or retrieve skins data from session state
if "skins_data" not in st.session_state:
    st.session_state["skins_data"] = {}

# --- LEFT PANEL: INPUTS ---
with st.sidebar:
    st.title("Shard Cost Calculator")
    st.subheader("Chest definition")
    num_skins = st.number_input("Skins included", min_value=1, max_value=5, value=1, step=1)
    days_available = st.number_input("Days available", min_value=1, max_value=60, value=21, step=1)
    shards_cost = st.number_input("Shards cost", min_value=1, max_value=500, value=30, step=1)
    key_shards_cost = st.number_input("Key shards cost", min_value=1, max_value=500, value=20, step=1)

    for skin_index in range(1, num_skins + 1):
        if skin_index not in st.session_state["skins_data"]:
            st.session_state["skins_data"][skin_index] = Skin(index=skin_index)
        current_skin = st.session_state["skins_data"][skin_index]

        st.subheader(f"Skin {skin_index}")
        current_skin.colors = st.number_input(
            f"Colors for Skin {skin_index}", min_value=1, max_value=10, value=current_skin.colors, key=f"colors_{skin_index}"
        )
        current_skin.pieces_per_color = st.number_input(
            f"Pieces per color for Skin {skin_index}", min_value=1, max_value=10, value=current_skin.pieces_per_color, key=f"pieces_{skin_index}"
        )
        current_skin.percentage_per_piece = st.number_input(
            f"Percentage per piece for Skin {skin_index}", min_value=0.5, max_value=100.0, value=current_skin.percentage_per_piece, key=f"percentage_{skin_index}", step=0.5
        )

        

# --- RIGHT PANEL: OUTPUTS ---
st.subheader("Results")

# Debugging: Display all skins data
total_percentage_sum = 0
with st.expander("Debugging Information"):
    for skin_id, skin_obj in st.session_state["skins_data"].items():
        st.subheader(str(skin_obj))
        st.write(f"Total pieces: {skin_obj.pieces}")
        display_percentage("Total skin percentage", skin_obj.total_percentage)
        total_percentage_sum += skin_obj.total_percentage
    st.subheader("Chest data")
    display_percentage("Total percentage sum of all skins", total_percentage_sum)

# Calculate button and results
if st.button("Calculate"):
    chest = Chest(days_available=days_available, 
                  skins=[st.session_state["skins_data"][i] for i in range(1, num_skins + 1)],
                    shards_cost=shards_cost,
                    key_shards_cost=key_shards_cost)
    st.write(f"Total pieces in chest: {chest.total_pieces()}")
    st.write(f"Total percentage in chest: {chest.total_percentage():.2f}%")
    chestSprint = ChestOpeningSprint(chest)
    
    avg_chests, avg_chests_per_color, avg_chests_per_skin = run_for_average(chest, n_runs=1000)
    shards_cost = chest.shards_needed(avg_chests)
    st.write(f"Average chests needed to complete all sets: {avg_chests:.2f}")
    st.write(f"Average shards needed to complete all sets: {shards_cost:.2f}")
    st.write(f"Average shards per day to complete all sets: {shards_cost / days_available:.2f}")
    for n_colors, chests in enumerate(avg_chests_per_color):
        if chests is not None and n_colors < 3:
            shards_cost = chest.shards_needed(chests)
            st.table({
                "Metric": ["Avg chests needed", "Avg shards cost", "Required Shards/Day"],
                f"{n_colors + 1} color sets": [
                    f"{chests:.2f}",
                    f"{shards_cost:.2f}",
                    f"{shards_cost / days_available:.2f}"
                ]
            })
    for n_skins, chests in enumerate(avg_chests_per_skin):
        if chests is not None:
            shards_cost = chest.shards_needed(chests)
            st.table({
                "Metric": ["Avg chests needed", "Avg shards cost", "Required Shards/Day"],
                f"{n_skins + 1} full skin sets": [
                    f"{chests:.2f}",
                    f"{shards_cost:.2f}",
                    f"{shards_cost / days_available:.2f}"
                ]
            })
    
    st.write(f"Average chests needed to complete each color set: {avg_chests_per_color}")
    st.write(f"Average chests needed to complete each skin: {avg_chests_per_skin}")
    st.success("Recalculated successfully!")