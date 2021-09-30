import re


def breakdown_recipients(grp):
    seen = set()
    to_send = [[]]

    for recip in grp:
        email = recip.get("email")
        email_no_alias = re.sub(r"[\!+](\S)*@", "@", email)

        if email_no_alias in seen:
            to_send.append([recip])
        else:
            seen.add(email_no_alias)
            to_send[0].append(recip)

    return to_send
