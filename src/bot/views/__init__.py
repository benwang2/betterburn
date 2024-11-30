from typing import Callable

import discord


class LinkView(discord.ui.View):
    def __init__(self, link_url, on_cancel):
        super().__init__(timeout=60)  # The view is active for 60 seconds
        self.add_item(
            discord.ui.Button(
                label="Authenticate",
                url=link_url,
                style=discord.ButtonStyle.blurple,
            )
        )
        self.on_cancel = on_cancel

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.danger)
    async def end_interaction(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        self.on_cancel()
        embed = discord.Embed(
            title="Linking session ended",
            description="You have canceled the linking process. If you wish to try again, use the `/link` command.",
            color=discord.Color.red(),
        )
        await interaction.response.edit_message(embed=embed, view=None)


class UnlinkView(discord.ui.View):
    def __init__(
        self,
        callback: Callable,
    ):
        super().__init__(timeout=60)
        self.callback = callback

    @discord.ui.button(label="Confirm", style=discord.ButtonStyle.green)
    async def end_interaction(
        self, interaction: discord.Interaction, button: discord.ui.Button
    ):
        embed = discord.Embed(
            title="Unlink completed",
            description="You have unlinked your steam account.",
            color=discord.Color.blurple(),
        )
        self.callback()
        await interaction.response.edit_message(embed=embed, view=None)
